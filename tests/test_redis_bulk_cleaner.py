#!/usr/bin/env python
import string
import uuid
from datetime import timedelta
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
    char_set = string.digits + string.ascii_letters + string.punctuation
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
]


@pytest.mark.parametrize("setup_data,cleanup_patterns,expected,not_expected", cleanup_tst_params)
def test_cleanup(redis_client, setup_data, cleanup_patterns, expected, not_expected):
    create_test_data(redis_client, setup_data)
    Cleaner(redis_client, cleanup_patterns, batch_size=10, cursor_backup_delta=None).cleanup(restart=True)
    for pattern in expected:
        assert redis_client.keys(pattern)
    for pattern in not_expected:
        assert not redis_client.keys(pattern)


def test_command_line_interface_help():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'redis_bulk_cleaner.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
