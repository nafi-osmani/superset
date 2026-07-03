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
"""Shared base filter classes for resource list endpoints.

These base classes consolidate duplicated filter logic that was previously
repeated across charts, dashboards, and datasets filters. Subclasses only
need to set ``model`` and ``arg_name`` to customize behavior.
"""

from __future__ import annotations

from typing import Any

from flask_appbuilder.models.sqla.filters import BaseFilter
from flask_babel import lazy_gettext as _
from sqlalchemy import and_, or_
from sqlalchemy.orm.query import Query

from superset.utils.core import get_user_id


class BaseCreatedByMeFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    """Filter resources created or changed by the current user."""

    name = _("Created by me")
    arg_name = ""
    model: Any = None

    def apply(self, query: Query, value: Any) -> Query:
        return query.filter(
            or_(
                self.model.created_by_fk  # pylint: disable=comparison-with-callable
                == get_user_id(),
                self.model.changed_by_fk  # pylint: disable=comparison-with-callable
                == get_user_id(),
            )
        )


class BaseHasCreatedByFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    """Filter resources that have (or lack) a created_by_fk value."""

    name = _("Has created by")
    arg_name = ""
    model: Any = None

    def apply(self, query: Query, value: Any) -> Query:
        if value is True:
            return query.filter(and_(self.model.created_by_fk.isnot(None)))
        if value is False:
            return query.filter(and_(self.model.created_by_fk.is_(None)))
        return query


class BaseCertifiedFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    """Filter resources by certification status using a ``certified_by`` column."""

    name = _("Is certified")
    arg_name = ""
    model: Any = None

    def apply(self, query: Query, value: Any) -> Query:
        if value is True:
            return query.filter(and_(self.model.certified_by.isnot(None)))
        if value is False:
            return query.filter(and_(self.model.certified_by.is_(None)))
        return query
