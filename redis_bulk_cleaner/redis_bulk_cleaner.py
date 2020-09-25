import re
from datetime import datetime, timedelta

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
        *patterns,
        batch_size=1000,
        cursor_backup_delta=timedelta(minutes=1),
        cursor_backup_expiration=timedelta(days=30),
    ):
        if not redis.connection_pool.connection_kwargs['decode_responses']:
            raise RuntimeError(f"{redis} should decode data (decode_responses=True)")

        self.redis = redis
        self.patterns = sorted(patterns)
        self.batch_size = batch_size
        self.cursor_backup_delta = cursor_backup_delta
        self.cursor_backup_expiration = cursor_backup_expiration

        self._regex = re.compile('^(?:' + '|'.join(
            re.escape(p).replace('\\*', '.+')
            for p in self.patterns
        ) + ')$')

    def cleanup(self, restart=False):
        last_backup_time = datetime.now()
        cursor = 0 if restart else self.redis.hget(*self._cursor_backup_key)
        cursor = int(cursor) if cursor else 0
        max_cursor = cursor
        redis_size = self.redis.dbsize()
        redis_size = int(1.1 * redis_size)  # To handle duplicates
        cursor_bar = tqdm(
            initial=convert_scan_cursor(cursor, max_cursor),
            total=redis_size,
            position=0, desc='Cursor', dynamic_ncols=True, unit='', smoothing=.01, unit_scale=1
        )
        redis_rows = tqdm(position=1, initial=0, desc='  Rows', dynamic_ncols=True, unit=' deleted',
                          smoothing=.01, unit_scale=1)
        while True:
            cursor, keys = self.redis.scan(cursor, count=self.batch_size)
            max_cursor = max(max_cursor, cursor)
            real_cursor = convert_scan_cursor(cursor, max_cursor)
            cursor_bar.update(real_cursor - cursor_bar.n)
            if not keys:
                continue
            keys = list(filter(self._regex.match, keys))
            if not keys:
                continue
            pipeline = self.redis.pipeline()
            pipeline.delete(*keys)
            if self.cursor_backup_delta is not None and datetime.now() - last_backup_time > self.cursor_backup_delta:
                pipeline.hset(*self._cursor_backup_key, cursor)
                pipeline.expire(self._cursor_backup_key[0], self.cursor_backup_expiration)
                last_backup_time = datetime.now()
            deleted = pipeline.execute()[0]
            redis_rows.update(deleted)
            if cursor == 0:
                break
        cursor_bar.close()
        redis_rows.close()

    @property
    def _cursor_backup_key(self):
        return 'redis_cleaner:cursor', ';'.join(self.patterns)
