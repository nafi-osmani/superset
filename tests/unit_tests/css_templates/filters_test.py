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
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy.orm.session import Session

from superset.css_templates.filters import CssTemplateAllTextFilter
from superset.models.core import CssTemplate


def test_css_template_filter_name() -> None:
    filter_ = CssTemplateAllTextFilter("template_name", SQLAInterface(CssTemplate))
    assert filter_.arg_name == "css_template_all_text"


def test_css_template_filter_apply_empty_value(session: Session) -> None:
    query = session.query(CssTemplate)
    filter_ = CssTemplateAllTextFilter("template_name", SQLAInterface(CssTemplate))
    result = filter_.apply(query, "")
    compiled = str(result.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" not in compiled


def test_css_template_filter_apply_none_value(session: Session) -> None:
    query = session.query(CssTemplate)
    filter_ = CssTemplateAllTextFilter("template_name", SQLAInterface(CssTemplate))
    result = filter_.apply(query, None)
    compiled = str(result.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" not in compiled


def test_css_template_filter_apply_with_value(session: Session) -> None:
    query = session.query(CssTemplate)
    filter_ = CssTemplateAllTextFilter("template_name", SQLAInterface(CssTemplate))
    result = filter_.apply(query, "dark")
    compiled = str(result.statement.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" in compiled.upper()
    assert "%dark%" in compiled


def test_css_template_filter_searches_template_name_and_css(
    session: Session,
) -> None:
    query = session.query(CssTemplate)
    filter_ = CssTemplateAllTextFilter("template_name", SQLAInterface(CssTemplate))
    result = filter_.apply(query, "test")
    compiled = str(result.statement.compile(compile_kwargs={"literal_binds": True}))
    assert compiled.upper().count("LIKE") == 2
