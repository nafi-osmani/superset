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
import logging

from superset.commands.base import BaseBulkDeleteCommand
from superset.commands.query.exceptions import (
    SavedQueryDeleteFailedError,
    SavedQueryNotFoundError,
)
from superset.daos.query import SavedQueryDAO

logger = logging.getLogger(__name__)


class DeleteSavedQueryCommand(BaseBulkDeleteCommand):
    dao = SavedQueryDAO
    not_found_error = SavedQueryNotFoundError

    def _get_delete_failed_error(self) -> type[Exception]:
        return SavedQueryDeleteFailedError
