Changelog
=========
05-23-19
~~~~~~~~
* Feature: Add a new command line argument to allow a user to specify a seed timeout time

11-11-18
~~~~~~~~
* Feature: Add a new command line argument to seed a session through the browser
* Change: Added python version detection to the manage script as well

10-13-18
~~~~~~~~
* Feature: Detect when user changes between Python versions during setup
* Bugfix: Setup process appears to finally be bug-free, screw python2 support

07-10-18
~~~~~~~~
* Feature: Added the ability to set the frequency when creating alerts
* Bugfix: Fixed frequency settings when using the mail delivery method

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