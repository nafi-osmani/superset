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

from superset.available_domains.schemas import AvailableDomainsSchema


def test_available_domains_schema_dump_with_domains() -> None:
    schema = AvailableDomainsSchema()
    result = schema.dump({"domains": ["https://example.com", "https://other.com"]})
    assert result == {"domains": ["https://example.com", "https://other.com"]}


def test_available_domains_schema_dump_empty_list() -> None:
    schema = AvailableDomainsSchema()
    result = schema.dump({"domains": []})
    assert result == {"domains": []}


def test_available_domains_schema_dump_none() -> None:
    schema = AvailableDomainsSchema()
    result = schema.dump({"domains": None})
    assert result == {"domains": None}


def test_available_domains_schema_load_valid() -> None:
    schema = AvailableDomainsSchema()
    result = schema.load({"domains": ["https://example.com"]})
    assert result == {"domains": ["https://example.com"]}


def test_available_domains_schema_load_empty() -> None:
    schema = AvailableDomainsSchema()
    result = schema.load({})
    assert result == {}


def test_available_domains_schema_load_invalid_type() -> None:
    schema = AvailableDomainsSchema()
    with pytest.raises(ValidationError):
        schema.load({"domains": "not-a-list"})
