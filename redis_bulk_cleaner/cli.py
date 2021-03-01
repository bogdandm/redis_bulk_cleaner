import sys
from datetime import timedelta

import click
import redis

from redis_bulk_cleaner.redis_bulk_cleaner import Cleaner


@click.command()
@click.argument('patterns', nargs=-1)
@click.option('--dry-run', '-D', is_flag=True, help='Do not delete keys just print them')
@click.option('--restart', '-R', is_flag=True, help='Restart SCAN operation (if --use-cursor-backups is enabled)')
@click.option('--use-regex', '-r', is_flag=True, help='By default patterns are redis-patterns (* equals any characters sequence including `:`). '
                                                      'If this flag is enabled then it will parse patterns as python regex expressions '
                                                      '(some escaping may still be needed base on your shell type)')
#
@click.option('--host', '-h', type=str, default='localhost', help='Redis host', show_default=True)
@click.option('--port', '-p', type=int, default=6379, help='Redis port', show_default=True)
@click.option('--db', type=int, default=0, help='Redis db', show_default=True)
@click.option('--password', '-P', type=str, default='', help='Redis password', show_default=True)
#
@click.option('--batch', '-b', type=int, default=500, help='Redis SCAN batch size', show_default=True)
@click.option('--sleep', '-s', type=int, default=0, help='(milliseconds) Sleep between DELETE commands to prevent high memory and cpu usage.')
@click.option('--disable-cursor-backups', is_flag=True, default=False, show_default=True, help='Save SCAN cursor in tmp redis key')
def main(patterns, host, port, db, password, batch, dry_run, restart, disable_cursor_backups, use_regex, sleep):
    assert patterns
    if not dry_run:
        click.echo('This tools will delete ANY key that matches any of the following pattern:\n'
                   '{}'.format(', '.join(patterns)))
        ans = click.prompt('Do you want to continue?', type=click.Choice(('y', 'n')), show_choices=True)
        if ans != 'y':
            return 0
    else:
        click.echo('Search for keys:\n'
                   '{}\n==========='.format(', '.join(patterns)))
    redis_client = redis.Redis(host=host, port=port, db=db, password=password or None,
                               decode_responses=True, socket_timeout=60)
    Cleaner(
        redis_client,
        patterns,
        use_regex_patterns=use_regex,
        batch_size=batch,
        sleep_between_batches=sleep,
        dry_run=dry_run,
        cursor_backup_delta=None if disable_cursor_backups else timedelta(minutes=1)
    ).cleanup(restart=restart)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
