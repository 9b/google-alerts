Python Google Alerts
====================
.. image:: https://readthedocs.org/projects/google-alerts/badge/?version=latest
    :target: http://google-alerts.readthedocs.io/en/latest/?badge=latest

.. image:: https://badge.fury.io/py/google-alerts.svg
    :target: https://badge.fury.io/py/google-alerts

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT


The `google-alerts` Python module provides an abstract interface for the Google Alerts service. Google does not provide an official API for this service, so interactions are done through web scripting.

Quick Start
-----------
**Install the library**:

``pip install google-alerts`` or ``python setup.py install``

**Save your configuration**:

``google-alerts setup --email <your.mail@foo.com> --password 'password'``

**Create a monitor**:

``google-alerts create --term "hello world" --delivery 'rss'``

**List monitors**:

``google-alerts list``

**Delete a monitor**:

``google-alerts delete --id '89e517961a3148c7:c395b7d271b4eccc:com:en:US'``

Sample Code
-----------

This sample code shows some of the range of functionality within the module::

    from google_alerts.google_alerts import GoogleAlerts

    # Create an instance
    ga = GoogleAlerts('your.email@gmail.com', '**password**')

    # Authenticate your user
    ga.authenticate()

    # List configured monitors
    ga.list()

    # Add a new monitor
    ga.create("Hello World", {'delivery': 'RSS'})

    # Modify an existing monitor
    ga.modify("89e517961a3148c7:c395b7d271b4eccc:com:en:US", {'delivery': 'RSS', 'monitor_match': 'ALL'})

    # Delete a monitor
    ga.delete("89e517961a3148c7:c395b7d271b4eccc:com:en:US")


Example Output
--------------

Below is an example monitor::

    [{
        "term": "hello world",
        "user_id": "09738342945634096720",
        "language": "en",
        "monitor_id": "89e517961a3148c7:c395b7d271b4eccc:com:en:US",
        "region": "US",
        "rss_link": "https://google.com/alerts/feeds/09738342945634096720/9663349274289663466",
        "delivery": "RSS",
        "match_type": "BEST"
    }]

Features
--------
* Add new monitors (RSS or Mail)
* Modify existing monitors
* Delete monitors by ID or term
* List all monitors with details

Changelog
---------
05-30-18
~~~~~~~~
* Change: Explicitly detect when a CAPTCHA is being thrown

05-28-18
~~~~~~~~
* Feature: Take advantage of the config file concept inside of the class
* Feature: Authenticate users with a session file if it's available
* Change: Tell Chrome to avoid using Javascript so we get the old form

05-25-18
~~~~~~~~
* Change: Added headers to all calls to look like less of a bot
* Bugfix: Wrapped a problem area when inspecting the forms in a page
* Bugfix: Handled setup error for Python3

04-29-18
~~~~~~~~
* Feature: Allow users to setup exact match queries
* Change: Added support for Python3
* Bugfix: Removed extra calls causing an error in the decrypt process

04-26-18
~~~~~~~~
* Feature: Added a command line utility to the code for easy testing
* Bugfix: Removed clobbering error inside of delete routine
