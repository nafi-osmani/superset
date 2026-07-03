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
from superset.css_templates.schemas import (
    get_delete_ids_schema,
    openapi_spec_methods_override,
)


def test_get_delete_ids_schema_structure() -> None:
    assert get_delete_ids_schema["type"] == "array"
    assert get_delete_ids_schema["items"] == {"type": "integer"}


def test_openapi_spec_methods_override_contains_crud() -> None:
    assert "get" in openapi_spec_methods_override
    assert "get_list" in openapi_spec_methods_override
    assert "post" in openapi_spec_methods_override
    assert "put" in openapi_spec_methods_override
    assert "delete" in openapi_spec_methods_override
    assert "info" in openapi_spec_methods_override


def test_openapi_spec_methods_override_summaries() -> None:
    assert (
        openapi_spec_methods_override["get"]["get"]["summary"] == "Get a CSS template"
    )
    assert (
        openapi_spec_methods_override["post"]["post"]["summary"]
        == "Create a CSS template"
    )
    assert (
        openapi_spec_methods_override["put"]["put"]["summary"]
        == "Update a CSS template"
    )
    assert (
        openapi_spec_methods_override["delete"]["delete"]["summary"]
        == "Delete a CSS template"
    )


def test_openapi_spec_get_list_has_description() -> None:
    get_list = openapi_spec_methods_override["get_list"]["get"]
    assert "summary" in get_list
    assert "description" in get_list
    assert "CSS templates" in get_list["summary"]
