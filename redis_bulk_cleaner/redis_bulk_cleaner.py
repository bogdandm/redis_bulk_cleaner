import re
from datetime import datetime, timedelta
from functools import partial
from time import sleep

import click
from tqdm import tqdm


def convert_scan_cursor(cursor, max_cursor):
    """
    See https://engineering.q42.nl/redis-scan-cursor/

    Apply mask from max_cursor and reverse bits order
    """
    N = len(bin(max_cursor)) - 2
    value = bin(cursor)[2:]
    s = ("{:>0%ss}" % N).format(value)
    return int(s[::-1], base=2)


def get_redis_size_from_max_cursor(max_cursor):
    return 2 ** (len(bin(max_cursor)) - 2 + 1)


class Cleaner:
    def __init__(
        self,
        redis,
        patterns,
        use_regex_patterns=False,
        batch_size=1000,
        sleep_between_batches=0,
        cursor_backup_delta=timedelta(minutes=1),
        cursor_backup_expiration=timedelta(days=30),
        dry_run=False
    ):
        if not redis.connection_pool.connection_kwargs['decode_responses']:
            raise RuntimeError("{} should decode data (decode_responses=True)".format(redis))

        self.redis = redis
        self.patterns = sorted(patterns)
        self.batch_size = batch_size
        self.cursor_backup_delta = cursor_backup_delta
        self.cursor_backup_expiration = cursor_backup_expiration
        self.dry_run = dry_run
        self.sleep = partial(sleep, sleep_between_batches / 1000) if sleep_between_batches else lambda: None

        self._regex = re.compile('^(?:' + '|'.join(
            p.strip()
            if use_regex_patterns
            else re.escape(p.strip()).replace('\\*', '.+')
            for p in self.patterns
        ) + ')$')

    def cleanup(self, restart=False):
        last_backup_time = datetime.now()
        cursor = 0 if restart else self.redis.hget(*self._cursor_backup_key)
        cursor = int(cursor) if cursor else 0
        max_cursor = cursor
        redis_size = self.redis.dbsize()
        redis_size = int(1.1 * redis_size)  # To handle duplicates
        if not self.dry_run:
            cursor_bar = tqdm(
                initial=convert_scan_cursor(cursor, max_cursor),
                total=redis_size,
                position=0, desc='Cursor', dynamic_ncols=True, unit='', smoothing=.01, unit_scale=1
            )
            redis_rows = tqdm(position=1, initial=0, desc='  Rows', dynamic_ncols=True, unit=' deleted',
                              smoothing=.01, unit_scale=1)
        started = False
        total_deleted = 0
        while cursor > 0 or not started:
            started = True
            cursor, keys = self.redis.scan(cursor, count=self.batch_size)

            if not self.dry_run:
                max_cursor = max(max_cursor, cursor)
                real_cursor = convert_scan_cursor(cursor, max_cursor)
                cursor_bar.update(real_cursor - cursor_bar.n)

            if not keys:
                continue
            keys = list(filter(self._regex.match, keys))
            if not keys:
                continue

            if not self.dry_run:
                deleted = self.redis.delete(*keys)
                if self.cursor_backup_delta is not None and datetime.now() - last_backup_time > self.cursor_backup_delta:
                    self.redis.hset(*self._cursor_backup_key, cursor)
                    self.redis.expire(self._cursor_backup_key[0], self.cursor_backup_expiration)
                    last_backup_time = datetime.now()
                total_deleted += deleted
                redis_rows.update(deleted)
                self.sleep()
            else:
                for key in keys:
                    click.echo(key)

        if not self.dry_run:
            cursor_bar.close()
            redis_rows.close()
            click.echo('\n{} keys cleaned'.format(total_deleted))

    @property
    def _cursor_backup_key(self):
        return 'redis_cleaner:cursor', ';'.join(self.patterns)
