#!/usr/bin/env python

import sys

from app import app
from app.database import init_db, insert_rand

def usage():
    print('''usage: %s [get_url|init_db|insert_rand]

    get_url
        Just print the url where the app will be reachable.

    init_db
        initialize the database. Existing data will be lost.

    insert_rand
        Will insert lot of random data to the database.

    Just start the app if no argument is passed.
    ''' % sys.argv[0])
    sys.exit(1)

def get_arg():
    if 2 == len(sys.argv) and sys.argv[1]:
        return sys.argv[1]

    else:
        return None

if '__main__' == __name__:
    host = app.config['HOST']
    port = app.config['PORT']
    debug = app.config['DEBUG']

    arg = get_arg()
    url = 'http://%s:%s' % (host, port)

    if arg:
        if 'get_url' == arg:
            print(url)
            sys.exit(0)

        elif 'init_db' == arg:
            init_db()
            sys.exit(0)

        elif 'insert_rand' == arg:
            insert_rand()
            sys.exit(0)

        else:
            usage()

    app.run(host=host,
            port=port,
            debug=debug)
