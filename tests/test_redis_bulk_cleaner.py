#!/usr/bin/env python
import string
import uuid
from datetime import timedelta
from itertools import chain
from random import randint, sample

import pytest
from click.testing import CliRunner

from redis_bulk_cleaner import cli
from redis_bulk_cleaner.redis_bulk_cleaner import Cleaner


@pytest.fixture
def redis_client():
    import redis
    client = redis.Redis(host='localhost', port=6379, db=9, decode_responses=True, socket_timeout=60)
    client.flushdb()
    return client


def test_connect(redis_client):
    """Sample pytest test function with the pytest fixture as an argument."""
    info = redis_client.info()
    assert info
    print(info)


def get_rand_string(n):
    char_set = string.digits + string.ascii_letters + ''.join(set(string.punctuation) - {':'})
    return ''.join(sample(char_set, 6))


def create_test_data(redis_client, data):
    for key, count in data.items():
        for _ in range(count):
            current_key = key \
                .replace('<int>', str(randint(1, 10 ** 6))) \
                .replace('<uuid>', uuid.uuid4().hex) \
                .replace('<str>', get_rand_string(randint(1, 100)))
            value = get_rand_string(64)
            redis_client.set(current_key, value, ex=timedelta(minutes=60))


# create_test_data values, cleanup patterns, expected keys patterns, not expected keys patterns
cleanup_tst_params = [
    pytest.param(
        {
            'user:<int>:session': 1000,
            'user:<int>:junk': 1000,
            'test': 1,
            'test_important': 1,
        },
        ['user:*:junk', 'test'],
        ['user:*:session', 'test_important'],
        ['user:*:junk', 'test'],
        id="simple"
    ),
    pytest.param(
        {
            'user:<int>:session': 1000,
            'user:<str>:session': 1000,
            'user:<uuid>:session': 1000,
            'user:<int>:delete_me': 1000,
            'user:<str>:delete_me': 1000,
            'user:<uuid>:delete_me': 1000,
        },
        ['user:*:delete_me'],
        ['user:*:session'],
        ['user:*:delete_me'],
        id="different_types"
    ),
]


@pytest.mark.parametrize("setup_data,cleanup_patterns,expected,not_expected", cleanup_tst_params)
def test_cleanup(redis_client, setup_data, cleanup_patterns, expected, not_expected):
    create_test_data(redis_client, setup_data)
    expected_keys = set(chain.from_iterable(redis_client.keys(pattern) for pattern in expected))
    Cleaner(redis_client, cleanup_patterns, batch_size=10, cursor_backup_delta=None).cleanup(restart=True)
    for pattern in expected:
        assert redis_client.keys(pattern)
    for pattern in not_expected:
        assert not redis_client.keys(pattern)
    assert not set(redis_client.keys('*')) - expected_keys


# create_test_data values, cleanup patterns, expected keys patterns, not expected keys patterns
cleanup_tst_params = [
    pytest.param(
        {
            'user:<int>:session': 1000,
            'user:<int>:junk': 1000,
            'test': 1,
            'test_important': 1,
        },
        ['user:\d+:junk', 'test'],
        ['user:*:session', 'test_important'],
        ['user:*:junk', 'test'],
        id="simple"
    ),
    pytest.param(
        {
            'user:<int>:session': 1000,
            'user:<str>:session': 1000,
            'user:<uuid>:session': 1000,
            'user:<int>:delete_me': 1000,
            'user:<str>:delete_me': 1000,
            'user:<uuid>:delete_me': 1000,
        },
        ['user:[^ :]+:delete_me'],
        ['user:*:session'],
        ['user:*:delete_me'],
        id="different_types"
    ),
]


@pytest.mark.parametrize("setup_data,cleanup_patterns,expected,not_expected", cleanup_tst_params)
def test_cleanup_regex_patterns(redis_client, setup_data, cleanup_patterns, expected, not_expected):
    create_test_data(redis_client, setup_data)
    expected_keys = set(chain.from_iterable(redis_client.keys(pattern) for pattern in expected))
    Cleaner(redis_client, cleanup_patterns, use_regex_patterns=True, batch_size=10, sleep_between_batches=1, cursor_backup_delta=None).cleanup(restart=True)
    for pattern in expected:
        assert redis_client.keys(pattern)
    for pattern in not_expected:
        assert not redis_client.keys(pattern)
    assert not set(redis_client.keys('*')) - expected_keys


def test_command_line_interface_help():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert 'Show this message and exit.' in help_result.output
