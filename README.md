```
$ pipx install git+https://github.com/alexpdp7/xbar-google-calendar
```

This code is heavily based on <https://developers.google.com/calendar/api/quickstart/python>.
Follow the instructions on that page to create a `credentials.json` file.

Run `xbar-google-calendar`; it will fail and write the path where it expects the `credentials.json` file.

To install on Argos:

```
$ ln -s $(which xbar-google-calendar) ~/.config/argos/calendar.10m
```
