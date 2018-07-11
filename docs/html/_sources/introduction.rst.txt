Getting Started
===============

**Install the library**:

``pip install google-alerts`` or ``python setup.py install``

**Save your configuration**:

``google-alerts setup --email <your.mail@foo.com> --password 'password'``

**Create a monitor**:

``google-alerts create --term "hello world" --delivery 'rss' --frequency 'realtime'``

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
