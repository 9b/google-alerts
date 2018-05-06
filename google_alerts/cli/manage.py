#!/usr/bin/env python
"""Perform administrative actions on Google Alerts."""
import base64
import json
import os
from google_alerts import GoogleAlerts
from argparse import ArgumentParser
import sys

PY2 = False
if sys.version_info[0] < 3:
    PY2 = True

__author__ = "Brandon Dixon"
__copyright__ = "Copyright, Brandon Dixon"
__credits__ = ["Brandon Dixon"]
__license__ = "MIT"
__maintainer__ = "Brandon Dixon"
__email__ = "brandon@9bplus.com"
__status__ = "BETA"


CONFIG_PATH = os.path.expanduser('~/.config/google_alerts')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
CONFIG_DEFAULTS = {'email': '', 'password': ''}


def obfuscate(p, action):
    """Obfuscate the auth details to avoid easy snatching.

    It's best to use a throw away account for these alerts to avoid having
    your authentication put at risk by storing it locally.
    """
    key = "ru7sll3uQrGtDPcIW3okutpFLo6YYtd5bWSpbZJIopYQ0Du0a1WlhvJOaZEH"
    s = list()
    if action == 'store':
        for i in range(len(p)):
            kc = key[i % len(key)]
            ec = chr((ord(p[i]) + ord(kc)) % 256)
            s.append(ec)
        return base64.urlsafe_b64encode("".join(s))
    else:
        e = base64.urlsafe_b64decode(p)
        for i in range(len(e)):
            kc = key[i % len(key)]
            if PY2:
                dc = chr((256 + ord(e[i]) - ord(kc)) % 256)
            else:
                dc = chr((256 + e[i] - ord(kc)) % 256)
            s.append(dc)
        return "".join(s)


def main():
    """Run the core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')
    setup_parser = subs.add_parser('setup')
    setup_parser.add_argument('-e', '--email', dest='email', required=True,
                              help='Email of the Google user.', type=str)
    setup_parser.add_argument('-p', '--password', dest='pwd', required=True,
                              help='Password of the Google user.', type=str)
    setup_parser = subs.add_parser('list')
    setup_parser = subs.add_parser('create')
    setup_parser.add_argument('-t', '--term', dest='term', required=True,
                              help='Term to store.', type=str)
    setup_parser.add_argument('--exact', dest='exact', action='store_true',
                              help='Exact matches only for term.')
    setup_parser.add_argument('-d', '--delivery', dest='delivery',
                              required=True, choices=['rss', 'mail'],
                              help='Delivery method of results.')
    setup_parser = subs.add_parser('delete')
    setup_parser.add_argument('--id', dest='term_id', required=True,
                              help='ID of the term to find for deletion.',
                              type=str)
    args = parser.parse_args()

    if args.cmd == 'setup':
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        if not os.path.exists(CONFIG_FILE):
            json.dump(CONFIG_DEFAULTS, open(CONFIG_FILE, 'w'), indent=4,
                      separators=(',', ': '))
        config = CONFIG_DEFAULTS
        config['email'] = args.email
        config['password'] = obfuscate(args.pwd, 'store')
        json.dump(config, open(CONFIG_FILE, 'w'), indent=4,
                  separators=(',', ': '))

    config = json.load(open(CONFIG_FILE))
    if config['password'] == '':
        raise Exception("Run setup before any other actions!")

    if args.cmd == 'list':
        config['password'] = obfuscate(str(config['password']), 'fetch')
        ga = GoogleAlerts(config['email'], config['password'])
        ga.authenticate()
        print(json.dumps(ga.list(), indent=4))

    if args.cmd == 'create':
        config['password'] = obfuscate(str(config['password']), 'fetch')
        ga = GoogleAlerts(config['email'], config['password'])
        ga.authenticate()
        monitor = ga.create(args.term, {'delivery': args.delivery.upper(),
                                        'exact': args.exact})
        print(json.dumps(monitor, indent=4))

    if args.cmd == 'delete':
        config['password'] = obfuscate(str(config['password']), 'fetch')
        ga = GoogleAlerts(config['email'], config['password'])
        ga.authenticate()
        result = ga.delete(args.term_id)
        if result:
            print("%s was deleted" % args.term_id)


if __name__ == '__main__':
    main()
