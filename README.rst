Python Google Alerts
====================
.. image:: https://readthedocs.org/projects/google-alerts/badge/?version=latest
    :target: http://google-alerts.readthedocs.io/en/latest/?badge=latest

.. image:: https://badge.fury.io/py/google-alerts.svg
    :target: https://badge.fury.io/py/google-alerts

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

    from google_alerts import GoogleAlerts

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
04-26-18
~~~~~~~~
* Feature: Added a command line utility to the code for easy testing
* Bugfix: Removed clobbering error inside of delete routine
