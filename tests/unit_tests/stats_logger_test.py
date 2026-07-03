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

from superset.stats_logger import BaseStatsLogger, DummyStatsLogger


def test_base_stats_logger_key_with_prefix() -> None:
    logger = BaseStatsLogger(prefix="myapp")
    assert logger.key(".requests") == "myapp.requests"


def test_base_stats_logger_key_without_prefix() -> None:
    logger = BaseStatsLogger(prefix="")
    assert logger.key("requests") == "requests"


def test_base_stats_logger_default_prefix() -> None:
    logger = BaseStatsLogger()
    assert logger.prefix == "superset"


def test_base_stats_logger_incr_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.incr("test")


def test_base_stats_logger_decr_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.decr("test")


def test_base_stats_logger_timing_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.timing("test", 1.0)


def test_base_stats_logger_gauge_not_implemented() -> None:
    logger = BaseStatsLogger()
    with pytest.raises(NotImplementedError):
        logger.gauge("test", 1.0)


def test_dummy_stats_logger_incr() -> None:
    logger = DummyStatsLogger()
    logger.incr("test_key")


def test_dummy_stats_logger_decr() -> None:
    logger = DummyStatsLogger()
    logger.decr("test_key")


def test_dummy_stats_logger_timing() -> None:
    logger = DummyStatsLogger()
    logger.timing("test_key", 42.0)


def test_dummy_stats_logger_gauge() -> None:
    logger = DummyStatsLogger()
    logger.gauge("test_key", 100.0)
