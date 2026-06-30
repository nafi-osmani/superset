# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Optional

from flask_appbuilder.security.sqla.models import User

from superset.commands.utils import compute_owner_list, populate_owner_list


class BaseCommand(ABC):
    """
    Base class for all Command like Superset Logic objects
    """

    @abstractmethod
    def run(self) -> Any:
        """
        Run executes the command. Can raise command exceptions
        :raises: CommandException
        """

    @abstractmethod
    def validate(self) -> None:
        """
        Validate is normally called by run to validate data.
        Will raise exception if validation fails
        :raises: CommandException
        """


class BaseBulkDeleteCommand(BaseCommand):
    """Shared base for bulk-delete commands that follow the pattern:

    1. Accept a list of model IDs.
    2. Validate that all models exist (raise *not_found_error*).
    3. Optionally check ownership (raise *forbidden_error*).
    4. Delete via the DAO.

    Subclasses must set:
      - ``dao``: DAO class with ``find_by_ids`` and ``delete`` methods.
      - ``not_found_error``: exception class raised when models are missing.

    Subclasses may set:
      - ``forbidden_error``: exception class raised when ownership check fails.
        When set, ownership is validated for each model. When ``None``,
        the ownership check is skipped.
    """

    dao: Any = None
    not_found_error: type[Exception]
    forbidden_error: type[Exception] | None = None

    def __init__(self, model_ids: list[int]) -> None:
        self._model_ids = model_ids
        self._models: Optional[list[Any]] = None

    def run(self) -> None:
        from superset.utils.decorators import on_error, transaction

        @transaction(
            on_error=partial(on_error, reraise=self._get_delete_failed_error())
        )
        def _run() -> None:
            self.validate()
            assert self._models
            self.dao.delete(self._models)

        _run()

    def validate(self) -> None:
        self._models = self.dao.find_by_ids(self._model_ids)
        if not self._models or len(self._models) != len(self._model_ids):
            raise self.not_found_error()

        if self.forbidden_error is not None:
            from superset import security_manager
            from superset.exceptions import SupersetSecurityException

            for model in self._models:
                try:
                    security_manager.raise_for_ownership(model)
                except SupersetSecurityException as ex:
                    raise self.forbidden_error() from ex

    def _get_delete_failed_error(self) -> type[Exception]:
        """Return the error to re-raise on transaction failure.

        Defaults to the generic DeleteFailedError. Subclasses that define a
        custom failure error can override this.
        """
        from superset.commands.exceptions import DeleteFailedError

        return DeleteFailedError


class CreateMixin:  # pylint: disable=too-few-public-methods
    @staticmethod
    def populate_owners(owner_ids: Optional[list[int]] = None) -> list[User]:
        """
        Populate list of owners, defaulting to the current user if `owner_ids` is
        undefined or empty. If current user is missing in `owner_ids`, current user
        is added unless belonging to the Admin role.

        :param owner_ids: list of owners by id's
        :raises OwnersNotFoundValidationError: if at least one owner can't be resolved
        :returns: Final list of owners
        """
        return populate_owner_list(owner_ids, default_to_user=True)


class UpdateMixin:
    @staticmethod
    def populate_owners(owner_ids: Optional[list[int]] = None) -> list[User]:
        """
        Populate list of owners. If current user is missing in `owner_ids`, current user
        is added unless belonging to the Admin role.

        :param owner_ids: list of owners by id's
        :raises OwnersNotFoundValidationError: if at least one owner can't be resolved
        :returns: Final list of owners
        """
        return populate_owner_list(owner_ids, default_to_user=False)

    @staticmethod
    def compute_owners(
        current_owners: Optional[list[User]],
        new_owners: Optional[list[int]],
    ) -> list[User]:
        """
        Handle list of owners for update events.

        :param current_owners: list of current owners
        :param new_owners: list of new owners specified in the update payload
        :returns: Final list of owners
        """
        return compute_owner_list(current_owners, new_owners)
