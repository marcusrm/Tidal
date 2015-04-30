#!/usr/bin/python2.7


PORT=8008
URL_PREFIX = '/%02d'%(PORT % 100)

PASSWORD_DB = 'static/passwords.db'
PASSWORD_SCHEMA = 'static/passwords.sql'
AMT_HIT_DB = 'static/amt_hit.db'
AMT_HIT_SCHEMA = 'static/amt_hit.sql'
SALT = 'static/salt.bin'
MAX_SIZE_USERNAME=32
MAX_SIZE_PASSWORD=32
MIN_SIZE_USERNAME=8
MIN_SIZE_PASSWORD=8


LOCAL_TESTING=False
