# Download emails

Save emails from an IMAP server into local files.


## Requirements

[PyYAML](http://pyyaml.org/) to load settings from a Yaml file.

The `settings_example.py` and `settings_example.yaml` need to be copied
and have the `_example` part removed.
These new files should be modified to contain local settings.


## Usage

Once that configuration is complete, you can run the main script:

	python download_emails.py


## Helpful articles and documentation

- [19.1. email - An email and MIME handling package](https://docs.python.org/3.4/library/email.html).
  Stores the raw content from IMAP in a wrapper class.

- [19.9. quopri - Encode and decode MIME quoted-printable data](https://docs.python.org/3.4/library/quopri.html)

- [21.15. imaplib - IMAP4 protocol client](https://docs.python.org/3.4/library/imaplib.html).
  Getting emails from folders within an IMAP server.

- [How to fetch an email body using imaplib in python?](http://stackoverflow.com/questions/2230037/how-to-fetch-an-email-body-using-imaplib-in-python)

- [How to understand the equal sign '=' symbol in IMAP email text?](http://stackoverflow.com/questions/15621510/how-to-understand-the-equal-sign-symbol-in-imap-email-text).
  Decode the MIME symbols in the email content (fixes soft line breaks).

- [INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4rev1](http://tools.ietf.org/html/rfc2060.html)

- [INTERNET MESSAGE ACCESS PROTOCOL - VERSION 4](http://tools.ietf.org/html/rfc1730.html)

- [Move an email in GMail with Python and imaplib](https://stackoverflow.com/questions/3527933/move-an-email-in-gmail-with-python-and-imaplib)

- [Python - imaplib IMAP example with Gmail](http://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/).
  This article in particular was very helpful as a starting point.
