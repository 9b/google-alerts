#!/usr/bin/env python
"""Abstract API over the Google Alerts service."""
import base64
import json
import logging
import os
import pickle
import requests
import requests.utils
import sys
from bs4 import BeautifulSoup


__author__ = "Brandon Dixon"
__copyright__ = "Copyright, Brandion Dixon"
__credits__ = ["Brandon Dixon"]
__license__ = "MIT"
__maintainer__ = "Brandon Dixon"
__email__ = "brandon@9bplus.com"
__status__ = "BETA"


PY2 = False
if sys.version_info[0] < 3:
    PY2 = True


class InvalidCredentials(Exception):
    """Exception for invalid credentials."""
    pass


class AccountCaptcha(Exception):
    """Exception for account CAPTCHA."""
    pass


class InvalidState(Exception):
    """Exception for invalid state."""
    pass


class StateParseFailure(Exception):
    """Exception for failing to parse state."""
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


def obfuscate(p, action):
    """Obfuscate the auth details to avoid easy snatching.

    It's best to use a throw away account for these alerts to avoid having
    your authentication put at risk by storing it locally.
    """
    key = "ru7sll3uQrGtDPcIW3okutpFLo6YYtd5bWSpbZJIopYQ0Du0a1WlhvJOaZEH"
    s = list()
    if action == 'store':
        if PY2:
            for i in range(len(p)):
                kc = key[i % len(key)]
                ec = chr((ord(p[i]) + ord(kc)) % 256)
                s.append(ec)
            return base64.urlsafe_b64encode("".join(s))
        else:
            return base64.urlsafe_b64encode(p.encode()).decode()
    else:
        if PY2:
            e = base64.urlsafe_b64decode(p)
            for i in range(len(e)):
                kc = key[i % len(key)]
                dc = chr((256 + ord(e[i]) - ord(kc)) % 256)
                s.append(dc)
            return "".join(s)
        else:
            e = base64.urlsafe_b64decode(p)
            return e.decode()


CONFIG_PATH = os.path.expanduser('~/.config/google_alerts')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.json')
SESSION_FILE = os.path.join(CONFIG_PATH, 'session')
CONFIG_DEFAULTS = {'email': '', 'password': '', 'py2': PY2}


class GoogleAlerts:

    NAME = "GoogleAlerts"
    LOG_LEVEL = logging.DEBUG
    LOGIN_URL = 'https://accounts.google.com/ServiceLogin?nojavascript=1'
    AUTH_URL = 'https://accounts.google.com/signin/challenge/sl/password'
    ALERTS_URL = 'https://www.google.com/alerts'
    TEST_URL = 'https://myaccount.google.com/?pli=1'
    TEST_KEY = 'CREATE YOUR GOOGLE ACCOUNT'
    CAPTCHA_KEY = 'captcha-container'
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

    def __init__(self, email=None, password=None):
        self._log = self._logger()
        self._email = email
        self._password = password
        self._is_authenticated = False
        self._state = None
        self._session = requests.session()
        self._config_bootstrap()

    def _config_bootstrap(self):
        """Go through and establish the defaults on the file system.

        The approach here was stolen from the CLI tool provided with the
        module. Idea being that the user should not always need to provide a
        username and password in order to run the script. If the configuration
        file is already present with valid data, then lets use it.
        """
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        if not os.path.exists(CONFIG_FILE):
            json.dump(CONFIG_DEFAULTS, open(CONFIG_FILE, 'w'), indent=4,
                      separators=(',', ': '))
        config = CONFIG_DEFAULTS
        if self._email and self._password:
            #  Save the configuration locally to pull later on
            config['email'] = self._email
            config['password'] = str(obfuscate(self._password, 'store'))
            self._log.debug("Caching authentication in config file")
            json.dump(config, open(CONFIG_FILE, 'w'), indent=4,
                      separators=(',', ': '))
        else:
            #  Load the config file and override the class
            config = json.load(open(CONFIG_FILE))
            if config.get('py2', PY2) != PY2:
                raise Exception("Python versions have changed. Please run `setup` again to reconfigure the client.")
            if config['email'] and config['password']:
                self._email = config['email']
                self._password = obfuscate(str(config['password']), 'fetch')
                self._log.debug("Loaded authentication from config file")

    def _session_check(self):
        """Attempt to authenticate the user through a session file.

        This process is done to avoid having to authenticate the user every
        single time. It uses a session file that is saved when a valid session
        is captured and then reused. Because sessions can expire, we need to
        test the session prior to calling the user authenticated. Right now
        that is done with a test string found in an unauthenticated session.
        This approach is not an ideal method, but it works.
        """
        if not os.path.exists(SESSION_FILE):
            self._log.debug("Session file does not exist")
            return False
        with open(SESSION_FILE, 'rb') as f:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
            self._session.cookies = cookies
            self._log.debug("Loaded cookies from session file")
        response = self._session.get(url=self.TEST_URL, headers=self.HEADERS)
        if self.TEST_KEY in str(response.content):
            self._log.debug("Session file appears invalid")
            return False
        self._is_authenticated = True
        self._process_state()
        return True

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

    def set_log_level(self, level):
        """Override the default log level of the class"""
        if level == 'info':
            level = logging.INFO
        if level == 'debug':
            level = logging.DEBUG
        if level == 'error':
            level = logging.ERROR
        self._log.setLevel(level)

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
            try:
                state = json.loads(i.text[25:-6])
                if state != "":
                    self._state = state
                    self._log.debug("State value set: %s" % self._state)
            except Exception as e:
                raise StateParseFailure("Google has changed their core protocol and a new parser must be built. Please file a bug at https://github.com/9b/google-alerts/issues.")
        return self._state

    def _build_payload(self, term, options):
        if 'delivery' not in options:
            raise InvalidConfig("`delivery` is required in options.")
        region = options.get('region', 'US')
        language = options.get('language', 'en')
        imatch_type = {v: k for k, v in self.MONITOR_MATCH_TYPE.items()}
        monitor_match = imatch_type[options.get('monitor_match', 'ALL')]
        ialert_freq = {v: k for k, v in self.ALERT_FREQ.items()}
        freq_option = options.get('alert_frequency', 'AT_MOST_ONCE_A_DAY')
        freq_option = ialert_freq[freq_option]
        if 'alert_frequency' not in options:
            options['alert_frequency'] = 'AT_MOST_ONCE_A_DAY'
        if options.get('exact', False):
            term = "\"%s\"" % term

        if options['delivery'] == 'RSS':
            payload = [None, [None, None, None, [None, term, "com", [None,
                       language, region], None, None, None, 0, 1], None,
                       monitor_match, [[None, 2, "", [], 1, "en-US", None,
                       None, None, None, None, "0", None, None,
                       self._state[2]]]]]
        else:
            if options['alert_frequency'] == 'AT_MOST_ONCE_A_DAY':
                payload = [None, [None, None, None, [None, term, "com", [None,
                           language, region], None, None, None, 0, 1], None,
                           monitor_match, [[None, 1, self._email, [None, None, 3],
                           freq_option, "en-US", None, None, None, None, None, "0",
                           None, None, self._state[2]]]]]
            elif options['alert_frequency'] == 'AS_IT_HAPPENS':
                payload = [None, [None, None, None, [None, term, "com", [None,
                           language, region], None, None, None, 0, 1], None,
                           monitor_match, [[None, 1, self._email, [], freq_option,
                           "en-US", None, None, None, None, None, "0",
                           None, None, self._state[2]]]]]
            elif options['alert_frequency'] == 'AT_MOST_ONCE_A_WEEK':
                payload = [None, [None, None, None, [None, term, "com", [None,
                           language, region], None, None, None, 0, 1], None,
                           monitor_match, [[None, 1, self._email, [None, None, 0, 3],
                           freq_option, "en-US", None, None, None, None, None, "0",
                           None, None, self._state[2]]]]]

        if options.get('action') == 'MODIFY':
            payload.insert(1, options.get('monitor_id'))
            if 'rss_id' in options:
                payload[2][6][0][11] = options['rss_id'].split('/')[-1]
        return payload

    def authenticate(self):
        """Authenticate the user and setup our state."""
        valid = self._session_check()
        if self._is_authenticated and valid:
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
        if self.CAPTCHA_KEY in str(response.content):
            raise AccountCaptcha('Google is forcing a CAPTCHA. To get around this issue, run the google-alerts with the seed option to open an interactive authentication session. Once authenticated, this module will cache your session and load that in the future')
        cookies = [x.name for x in response.cookies]
        if 'SIDCC' not in cookies:
            raise InvalidCredentials("Email or password was incorrect.")
        with open(SESSION_FILE, 'wb') as f:
            cookies = requests.utils.dict_from_cookiejar(self._session.cookies)
            pickle.dump(cookies, f, protocol=2)
            self._log.debug("Saved session to disk for future reference")
        self._log.debug("User successfully authenticated")
        self._is_authenticated = True
        self._process_state()
        return

    def list(self, term=None):
        """List alerts configured for the account.

        At the time of processing, here are several state examples:

        - ['062bc676ab9e9d9b:5a96b75728adb9d4:com:en:US', [None, None, ['email_aih_all', 'com', ['en', 'US'], None, None, None, False], None, 2, [[1, 'XXX@gmail.com', [], 1, 'en-US', 1, None, None, None, None, '7290377213681086747', None, None, 'AB2Xq4g1vxP5nJCT4SVMp8-8CeYubB7G0yQdZnM']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:eb34fff1681232ae:com:en:US', [None, None, ['email_aih_best', 'com', ['en', 'US'], None, None, None, False], None, 3, [[1, 'XXX@gmail.com', [], 1, 'en-US', 1, None, None, None, None, '11048899972761343896', None, None, 'AB2Xq4ibeyRSs4e6CQEjGTYWRyQgHftJgjkGmdE']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:029a12ab092e4d48:com:en:US', [None, None, ['email_d_all', 'com', ['en', 'US'], None, None, None, False], None, 2, [[1, 'XXX@gmail.com', [None, 18], 2, 'en-US', 1, None, None, None, None, '13677540305540568185', None, None, 'AB2Xq4iqyPDNCX_G_ZahmtXr3Ev1Xxk71J3A9o8']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:be633f8e2d769ed1:com:en:US', [None, None, ['email_d_best', 'com', ['en', 'US'], None, None, None, False], None, 3, [[1, 'XXX@gmail.com', [None, 18], 2, 'en-US', 1, None, None, None, None, '3165773263851675895', None, None, 'AB2Xq4gAyl3SR-5AKh3NstCHFf3I5tOCH_8Te98']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:4064fca73997bea1:com:en:US', [None, None, ['email_w_all', 'com', ['en', 'US'], None, None, None, False], None, 2, [[1, 'XXX@gmail.com', [None, 18, 0], 3, 'en-US', 1, None, None, None, None, '1277526588871069988', None, None, 'AB2Xq4jNqRCDJaqIvPfZTI6Sos2MMPb5q_6jS14']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:ed3adf6fd0968cb0:com:en:US', [None, None, ['email_w_best', 'com', ['en', 'US'], None, None, None, False], None, 3, [[1, 'XXX@gmail.com', [None, 18, 0], 3, 'en-US', 1, None, None, None, None, '11943490843312281977', None, None, 'AB2Xq4gvnjg6s07wCxTs4Ag8_6uOC0u9-7Aiu8E']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:a92eace4d0488209:com:en:US', [None, None, ['rss_aih_best', 'com', ['en', 'US'], None, None, None, False], None, 3, [[2, '', [], 1, 'en-US', 1, None, None, None, None, '10457927733922767031', None, None, 'AB2Xq4jZ1IPZLS44ZpaXYn8Fh46euu8_so_2k7k']]], '06449491676132715360']
        - ['062bc676ab9e9d9b:ac4752c338e8c363:com:en:US', [None, None, ['rss_all', 'com', ['en', 'US'], None, None, None, False], None, 2, [[2, '', [], 1, 'en-US', 1, None, None, None, None, '17387577876633356534', None, None, 'AB2Xq4h1wQcVxLfb0s835KmJWdw7bfUzzwpjUrg']]], '06449491676132715360']
        """
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        self._process_state()
        if not self._state[0]:
            self._log.info("No monitors have been created yet.")
            return list()

        monitors = list()
        try:
            for monitor in self._state[0][0]:
                obj = dict()
                obj['monitor_id'] = monitor[0]
                obj['user_id'] = monitor[-1]
                obj['term'] = monitor[1][2][0]
                if term and obj['term'] != term:
                    continue
                obj['language'] = monitor[1][2][2][0]
                obj['region'] = monitor[1][2][2][1]
                obj['delivery'] = self.DELIVERY[monitor[1][5][0][0]]
                obj['match_type'] = self.MONITOR_MATCH_TYPE[monitor[1][4]]
                if obj['delivery'] == 'MAIL':
                    obj['alert_frequency'] = self.ALERT_FREQ[monitor[1][5][0][3]]
                    obj['email_address'] = monitor[1][5][0][1]
                else:
                    rss_id = monitor[1][5][0][10]
                    url = "https://google.com/alerts/feeds/{uid}/{fid}"
                    obj['rss_link'] = url.format(uid=obj['user_id'], fid=rss_id)
                monitors.append(obj)
        except Exception as e:
            raise StateParseFailure("Observed state differs from parser. Please file a bug at https://github.com/9b/google-alerts/issues.")
        return monitors

    def create(self, term, options):
        """Create a monitor using passed configuration."""
        if not self._state:
            raise InvalidState("State was not properly obtained from the app")
        options['action'] = 'CREATE'
        payload = self._build_payload(term, options)
        url = self.ALERTS_CREATE_URL.format(requestX=self._state[2])
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
        url = self.ALERTS_MODIFY_URL.format(requestX=self._state[2])
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
        url = self.ALERTS_DELETE_URL.format(requestX=self._state[2])
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
        url = self.ALERTS_DELETE_URL.format(requestX=self._state[2])
        self._log.debug("Deleting alert using: %s" % url)
        payload = [None, monitor_id]
        params = json.dumps(payload, separators=(',', ':'))
        data = {'params': params}
        response = self._session.post(url, data=data, headers=self.HEADERS)
        if response.status_code != 200:
            raise ActionError("Failed to delete by term: %s"
                              % response.content)
        return True
