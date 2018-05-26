#!/usr/bin/env python
"""Abstract API over the Google Alerts service."""
import json
import logging
import requests
import sys
from bs4 import BeautifulSoup


__author__ = "Brandon Dixon"
__copyright__ = "Copyright, Brandion Dixon"
__credits__ = ["Brandon Dixon"]
__license__ = "MIT"
__maintainer__ = "Brandon Dixon"
__email__ = "brandon@9bplus.com"
__status__ = "BETA"


class InvalidCredentials(Exception):
    """Exception for invalid credentials."""
    pass


class InvalidState(Exception):
    """Exception for invalid state."""
    pass


class MonitorNotFound(Exception):
    """Exception for missing monitors."""
    pass


class InvalidConfig(Exception):
    """Exception for invalid configurations."""
    pass


class ActionError(Exception):
    """Exception for generic failures on action."""
    pass


class GoogleAlerts:

    NAME = "GoogleAlerts"
    LOG_LEVEL = logging.INFO
    LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    AUTH_URL = 'https://accounts.google.com/signin/challenge/sl/password'
    ALERTS_URL = 'https://www.google.com/alerts'
    ALERTS_MODIFY_URL = 'https://www.google.com/alerts/modify?x={requestX}'
    ALERTS_CREATE_URL = 'https://www.google.com/alerts/create?x={requestX}'
    ALERTS_DELETE_URL = 'https://www.google.com/alerts/delete?x={requestX}'
    MONITOR_MATCH_TYPE = {
        2: 'ALL',
        3: 'BEST'
    }
    ALERT_FREQ = {
        1: 'AS_IT_HAPPENS',
        2: 'AT_MOST_ONCE_A_DAY',
        3: 'AT_MOST_ONCE_A_WEEK',
    }
    DELIVERY = {
        1: 'MAIL',
        2: 'RSS'
    }
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, email, password):
        self._log = self._logger()
        self._email = email
        self._password = password
        self._is_authenticated = False
        self._state = None
        self._session = requests.session()

    def _logger(self):
        """Create a logger to be used between processes.

        :returns: Logging instance.
        """
        logger = logging.getLogger(self.NAME)
        logger.setLevel(self.LOG_LEVEL)
        shandler = logging.StreamHandler(sys.stdout)
        fmt = '\033[1;32m%(levelname)-5s %(module)s:%(funcName)s():'
        fmt += '%(lineno)d %(asctime)s\033[0m| %(message)s'
        shandler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(shandler)
        return logger

    def _process_state(self):
        """Process the application state configuration.

        Google Alerts manages the account information and alert data through
        some custom state configuration. Not all values have been completely
        enumerated.
        """
        self._log.debug("Capturing state from the request")
        response = self._session.get(url=self.ALERTS_URL, headers=self.HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        for i in soup.findAll('script'):
            if i.text.find('window.STATE') == -1:
                continue
            state = json.loads(i.text[15:-1])
            if state != "":
                self._state = state
                self._log.debug("State value set: %s" % self._state)
        return self._state

    def _build_payload(self, term, options):
        if 'delivery' not in options:
            raise InvalidConfig("`delivery` is required in options.")
        region = options.get('region', 'US')
        language = options.get('language', 'en')
        imatch_type = {v: k for k, v in self.MONITOR_MATCH_TYPE.items()}
        monitor_match = imatch_type[options.get('monitor_match', 'BEST')]
        ialert_freq = {v: k for k, v in self.ALERT_FREQ.items()}
        freq_option = options.get('alert_frequency', 'AT_MOST_ONCE_A_DAY')
        freq_option = ialert_freq[freq_option]
        if options.get('exact', False):
            term = "\"%s\"" % term

        if options['delivery'] == 'RSS':
            payload = [None, [None, None, None, [None, term, "com", [None,
                       language, region], None, None, None, 0, 1], None,
                       monitor_match, [[None, 2, "", [], 1, "en-US", None,
                       None, None, None, None, "0", None, None,
                       self._state[3]]]]]
        else:
            payload = [None, [None, None, None, [None, term, "com", [None,
                       language, region], None, None, None, 0, 1], None,
                       monitor_match, [[None, 1, self._email, [None, None, 3],
                       freq_option, "en-US", None, None, None, None, None, "0",
                       None, None, self._state[3]]]]]

        if options.get('action') == 'MODIFY':
            payload.insert(1, options.get('monitor_id'))
            if 'rss_id' in options:
                payload[2][6][0][11] = options['rss_id'].split('/')[-1]
        return payload

    def authenticate(self):
        """Authenticate the user and setup our state."""
        if self._is_authenticated:
            self._log.debug("[!] User has already authenticated")
            return
        init = self._session.get(url=self.LOGIN_URL, headers=self.HEADERS)
        soup = BeautifulSoup(init.content, "html.parser")
        soup_login = soup.find('form').find_all('input')
        post_data = dict()
        for u in soup_login:
            if u.has_attr('name') and u.has_attr('value'):
                post_data[u['name']] = u['value']
        post_data['Email'] = self._email
        post_data['Passwd'] = self._password
        response = self._session.post(url=self.AUTH_URL, data=post_data,
                                      headers=self.HEADERS)
        cookies = [x.name for x in response.cookies]
        if 'SIDCC' not in cookies:
            raise InvalidCredentials("Email or password was incorrect or Google is forcing a CAPTCHA.")
        self._log.debug("User successfully authenticated")
        self._is_authenticated = True
        self._process_state()
        return

    def list(self, term=None):
        """List alerts configured for the account."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        self._process_state()
        if not self._state[1]:
            self._log.info("No monitors have been created yet.")
            return list()

        monitors = list()
        for monitor in self._state[1][1]:
            obj = dict()
            obj['monitor_id'] = monitor[1]
            obj['user_id'] = monitor[-1]
            obj['term'] = monitor[2][3][1]
            if term and obj['term'] != term:
                continue
            obj['language'] = monitor[2][3][3][1]
            obj['region'] = monitor[2][3][3][2]
            obj['delivery'] = self.DELIVERY[monitor[2][6][0][1]]
            obj['match_type'] = self.MONITOR_MATCH_TYPE[monitor[2][5]]
            if obj['delivery'] == 'MAIL':
                obj['alert_frequency'] = self.ALERT_FREQ[monitor[2][6][0][4]]
                obj['email_address'] = monitor[2][6][0][2]
            else:
                rss_id = monitor[2][6][0][11]
                url = "https://google.com/alerts/feeds/{uid}/{fid}"
                obj['rss_link'] = url.format(uid=obj['user_id'], fid=rss_id)
            monitors.append(obj)
        return monitors

    def create(self, term, options):
        """Create a monitor using passed configuration."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        options['action'] = 'CREATE'
        payload = self._build_payload(term, options)
        url = self.ALERTS_CREATE_URL.format(requestX=self._state[3])
        self._log.debug("Creating alert using: %s" % url)
        params = json.dumps(payload, separators=(',', ':'))
        data = {'params': params}
        response = self._session.post(url, data=data, headers=self.HEADERS)
        if response.status_code != 200:
            raise ActionError("Failed to create monitor: %s"
                              % response.content)
        if options.get('exact', False):
            term = "\"%s\"" % term
        return self.list(term)

    def modify(self, monitor_id, options):
        """Create a monitor using passed configuration."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        monitors = self.list()  # Get the latest set of monitors
        obj = None
        for monitor in monitors:
            if monitor_id != monitor['monitor_id']:
                continue
            obj = monitor
        if not monitor_id:
            raise MonitorNotFound("No monitor was found with that term.")
        options['action'] = 'MODIFY'
        options.update(obj)
        payload = self._build_payload(obj['term'], options)
        url = self.ALERTS_MODIFY_URL.format(requestX=self._state[3])
        self._log.debug("Modifying alert using: %s" % url)
        params = json.dumps(payload, separators=(',', ':'))
        data = {'params': params}
        response = self._session.post(url, data=data, headers=self.HEADERS)
        if response.status_code != 200:
            raise ActionError("Failed to create monitor: %s"
                              % response.content)
        return self.list()

    def delete(self, monitor_id):
        """Delete a monitor by ID."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        monitors = self.list()  # Get the latest set of monitors
        bit = None
        for monitor in monitors:
            if monitor_id != monitor['monitor_id']:
                continue
            bit = monitor['monitor_id']
        if not bit:
            raise MonitorNotFound("No monitor was found with that term.")
        url = self.ALERTS_DELETE_URL.format(requestX=self._state[3])
        self._log.debug("Deleting alert using: %s" % url)
        payload = [None, monitor_id]
        params = json.dumps(payload, separators=(',', ':'))
        data = {'params': params}
        response = self._session.post(url, data=data, headers=self.HEADERS)
        if response.status_code != 200:
            raise ActionError("Failed to delete by ID: %s"
                              % response.content)
        return True

    def delete_by_term(self, term):
        """Delete an alert by term."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        monitors = self.list()  # Get the latest set of monitors
        monitor_id = None
        for monitor in monitors:
            if term != monitor['term']:
                continue
            monitor_id = monitor['monitor_id']
        if not monitor_id:
            raise MonitorNotFound("No monitor was found with that term.")
        url = self.ALERTS_DELETE_URL.format(requestX=self._state[3])
        self._log.debug("Deleting alert using: %s" % url)
        payload = [None, monitor_id]
        params = json.dumps(payload, separators=(',', ':'))
        data = {'params': params}
        response = self._session.post(url, data=data, headers=self.HEADERS)
        if response.status_code != 200:
            raise ActionError("Failed to delete by term: %s"
                              % response.content)
        return True
