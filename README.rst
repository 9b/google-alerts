Python Google Alerts
====================
The `google-alerts` Python module provides an abstract interface for the Google Alerts service. Google does not provide an official API for this service, so interactions are done through web scripting.

Getting Started
---------------
To be added.


Actions
-------
**Getting an instance**:

``ga = GoogleAlerts('your.email@gmail.com', '**password**')``

**Authenticating your user (does not support 2FA)**:

``ga.authenticate()``

**Listing monitors**:

``ga.list()``

**Example monitor listing**::

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

**Adding a new monitor**:

``ga.create("Hello World", {'delivery': 'RSS'})``

**Modify an existing monitor**:

``ga.modify("89e517961a3148c7:c395b7d271b4eccc:com:en:US", {'delivery': 'RSS', 'monitor_match': 'ALL'})``

**Delete a monitor**:

``ga.delete("89e517961a3148c7:c395b7d271b4eccc:com:en:US")``

Features
--------
* Add new monitors (RSS or Mail)
* Modify existing monitors
* Delete monitors by ID or term
* List all monitors with details

Changelog
---------
To be added.
