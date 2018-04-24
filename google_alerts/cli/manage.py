#!/usr/bin/env python
"""Perform administrative actions on Google Alerts."""
__author__ = "Brandon Dixon"
__copyright__ = "Copyright, Brandon Dixon"
__credits__ = ["Brandon Dixon"]
__license__ = "MIT"
__maintainer__ = "Brandon Dixon"
__email__ = "brandon@9bplus.com"
__status__ = "BETA"

import sys
from google_alerts.google_alerts import GoogleAlerts
from argparse import ArgumentParser


def main():
    """Run the core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')
    raise Exception("To Be Completed.")


if __name__ == '__main__':
    main()
