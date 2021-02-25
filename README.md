# redis-bulk-cleaner

![Python](https://img.shields.io/pypi/pyversions/redis_bulk_cleaner)
[![PyPi](https://img.shields.io/pypi/v/redis_bulk_cleaner.svg)](https://pypi.python.org/pypi/redis_bulk_cleaner)
[![image](https://img.shields.io/travis/bogdandm/redis_bulk_cleaner.svg)](https://travis-ci.com/bogdandm/redis_bulk_cleaner)

Deletes keys from [Redis](https://redis.io/) database in bulk.

## Features

* Built for very large scale databases (10Gb+, 100 000 000+ keys)
* Uses SCAN operation so it is safe to run it without downtime
* Could process multiple patterns using only one SCAN operation
* Has option to search for given patterns, but not delete them

## Usage


Install it via [PyPi](https://pypi.python.org/pypi/redis_bulk_cleaner)
```
pip install redis_bulk_cleaner
```

Firstly check what are you going to delete with `--dry-run` option:
```
$ redis_bulk_cleaner 'test:unsubscribe_token:*' 'test:session:*' --dry-run
Search for keys:
test:unsubscribe_token:*, test:session:*
===========
test:unsubscribe_token:NDCivQ45KQcTghpS
test:session:NDCivQ45KQcTghpS
test:unsubscribe_token:9SBQ1YsDPuTETWBS
test:unsubscribe_token:MckwaZGER1GiVjoX
test:session:9SBQ1YsDPuTETWBS
test:session:MckwaZGER1GiVjoX
```

You could pass as many patterns as you want. Only overhead will be Regex matching slowdown.

Then to actually delete keys run it without `--dry-run` option:
```
$ redis_bulk_cleaner 'test:unsubscribe_token:*' 'test:session:*'
This tools will delete ANY key that matches any of the following pattern:
test:unsubscribe_token:*, test:session:*
Do you want to continue? (y, n): y
...
6 keys cleaned
```

Be ware: it uses regex matching so `test*` will also match `test_other:key`.
However any special symbols like `.?` will be escaped.

[![asciicast](https://asciinema.org/a/A88rPFJcc5eRo54YDtiaTgeOW.svg)](https://asciinema.org/a/A88rPFJcc5eRo54YDtiaTgeOW)

Note: because of SCAN behaviour it is not possible to calculate accurate estimate/percentage.
Progress bar could go beyond 100%.

* `-D`, `--dry-run` - Do not delete keys just print them
    * **Default**: disabled
* `-r`, `--use-regex` - By default patterns are redis-patterns (`*` equals any characters sequence including `:`).
  If this flag is enabled then it will parse patterns as python regex expressions (some escaping may still be needed base on your shell type)
    * **Default**: disabled
* `-s`, `--sleep` - (milliseconds) Sleep between DELETE commands to prevent high memory and cpu usage. Disabled by default.
* `-h`, `--host` - Redis server host
    * **Default**: `localhost`
* `-p`, `--port` - Redis server port
    * **Default**: `6379`
* `--db` - Redis server db
    * **Default**: `0`
* `-P`, `--password` - Redis server password
    * **Default**: No password
* `-b`, '--batch' - Redis SCAN batch size
    * Too small value will cause slowdown, too high value could lead to memory issues/timeouts
    * **Default**: `500`
* `--disable-cursor-backups`
    * By default current scan position is saving to temporary redis variable (`redis_cleaner:cursor`)
      so it will continue from same place after restart (in case of crash/network issues/etc)
    * **Default**: Enabled

Also see `redis_bulk_cleaner --help`

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.

----

Free software: MIT license
