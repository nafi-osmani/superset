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
import pytest
from marshmallow import ValidationError

from superset.cachekeys.schemas import CacheInvalidationRequestSchema, Datasource
from superset.utils.core import DatasourceType


def test_datasource_schema_load_valid() -> None:
    schema = Datasource()
    result = schema.load(
        {
            "database_name": "my_db",
            "datasource_name": "my_table",
            "schema": "public",
            "datasource_type": DatasourceType.TABLE.value,
        }
    )
    assert result["database_name"] == "my_db"
    assert result["datasource_name"] == "my_table"
    assert result["schema"] == "public"
    assert result["datasource_type"] == DatasourceType.TABLE.value


def test_datasource_schema_load_with_catalog() -> None:
    schema = Datasource()
    result = schema.load(
        {
            "datasource_type": DatasourceType.TABLE.value,
            "catalog": "my_catalog",
        }
    )
    assert result["catalog"] == "my_catalog"


def test_datasource_schema_load_invalid_type() -> None:
    schema = Datasource()
    with pytest.raises(ValidationError, match="Must be one of"):
        schema.load({"datasource_type": "invalid_type"})


def test_datasource_schema_load_missing_required() -> None:
    schema = Datasource()
    with pytest.raises(ValidationError):
        schema.load({"database_name": "my_db"})


def test_cache_invalidation_schema_load_with_uids() -> None:
    schema = CacheInvalidationRequestSchema()
    result = schema.load({"datasource_uids": ["uid1", "uid2"]})
    assert result["datasource_uids"] == ["uid1", "uid2"]


def test_cache_invalidation_schema_load_with_datasources() -> None:
    schema = CacheInvalidationRequestSchema()
    result = schema.load(
        {
            "datasources": [
                {
                    "database_name": "db1",
                    "datasource_name": "table1",
                    "schema": "public",
                    "datasource_type": DatasourceType.TABLE.value,
                }
            ]
        }
    )
    assert len(result["datasources"]) == 1
    assert result["datasources"][0]["database_name"] == "db1"


def test_cache_invalidation_schema_load_with_both() -> None:
    schema = CacheInvalidationRequestSchema()
    result = schema.load(
        {
            "datasource_uids": ["uid1"],
            "datasources": [
                {
                    "datasource_type": DatasourceType.TABLE.value,
                    "datasource_name": "t1",
                }
            ],
        }
    )
    assert result["datasource_uids"] == ["uid1"]
    assert len(result["datasources"]) == 1


def test_cache_invalidation_schema_load_empty() -> None:
    schema = CacheInvalidationRequestSchema()
    result = schema.load({})
    assert result == {}


def test_cache_invalidation_schema_load_invalid_uid_type() -> None:
    schema = CacheInvalidationRequestSchema()
    with pytest.raises(ValidationError):
        schema.load({"datasource_uids": "not-a-list"})
