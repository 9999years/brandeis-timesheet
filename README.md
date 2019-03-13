# Timesheet generation for Brandeis University

A script to automatically generate timesheets from Google calendar events —
you’re already logging your work schedule in Google calendar, so why not
make transferring that to your timesheet painless?

# Dependencies

- Python 3.7
- The Python modules in `requirements.txt`
- `latexmk` and `xelatex`
- A Google developer application (see [“Google
    credentials”](#google-credentials) below)

# Usage

Make sure to tweak `settings.ini`, which contains all of the application
configuration!

`./render.sh` will update the project and its dependencies, generate a
timesheet, and run LaTeX to render it to a PDF.

`./email.sh` will run `./render.sh` and then run `make_email.py --send` to send
an email from your Gmail account.

A sample `crontab` line might look like:

    # Run at 6PM on Friday (5th day of week)
    0 18 * * 5 cd /home/user/.../brandeis-timesheet && ./email.sh

# Google credentials

To get some Google credentials you'll need to do a few things:

1. [Create a project][proj] in the Google Cloud Platform. There's a quota of
   like 12 projects but considering the calendar read limit of 1,000,000
   requests / day I think you’ll be OK. Make sure to enable the calendar API and the Gmail API.
2. [Download your project's credentials][creds], listed under OAuth 2.0 client
   IDs, by clicking the download icon or the app name and then the download
   button. Google has the JSON prepared for you, there's no reason to mess with
   it.
3. Rename the downloaded file (something like
   `client_secret_{YOUR_CLIENT_ID}.apps.googleusercontent.com`) to
   `client_secrets.json`, or whatever the value of `GOOGLE_CLIENT_SECRETS` in
   `settings.ini` is.
4. Run `python3.7 creds.py`, which will open your default browser, prompting
   you to log in. This generates the second set of OAuth keys, stored in
   `token.pickle` (`GOOGLE_TOKEN_PICKLE`). You’re done!

[gcal]: https://console.cloud.google.com/apis/dashboard
[creds]: https://console.cloud.google.com/apis/credentials
[proj]: https://console.cloud.google.com/projectcreate
