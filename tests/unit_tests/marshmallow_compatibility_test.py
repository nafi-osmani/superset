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
from superset.marshmallow_compatibility import _looks_like_fab_field


def test_looks_like_fab_field_single_word() -> None:
    assert _looks_like_fab_field("owner") is True


def test_looks_like_fab_field_snake_case_relationship() -> None:
    assert _looks_like_fab_field("created_by") is True


def test_looks_like_fab_field_with_digits() -> None:
    assert _looks_like_fab_field("col_2_value") is True


def test_looks_like_fab_field_leading_underscore() -> None:
    assert _looks_like_fab_field("_internal") is False


def test_looks_like_fab_field_empty() -> None:
    assert _looks_like_fab_field("") is False


def test_looks_like_fab_field_special_chars() -> None:
    assert _looks_like_fab_field("col-name") is False


def test_looks_like_fab_field_dotted_name() -> None:
    assert _looks_like_fab_field("a.b") is False
