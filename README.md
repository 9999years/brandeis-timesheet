# Timesheet generation for Brandeis University

A script to automatically generate timesheets from Google calendar events —
you’re already logging your work schedule in Google calendar, so why not
make transferring that to your timesheet painless?

# Google credentials

To get some Google credentials you'll need to do a few things:

1. [Create a project][proj] in the Google Cloud Platform. There's a quota of
   like 12 projects but considering the calendar read limit of 1,000,000
   requests / day I think you’ll be OK.
2. [Download your project's credentials][creds], listed under OAuth 2.0 client
   IDs, by clicking the download icon or the app name and then the download
   button. Google has the JSON prepared for you, there's no reason to mess with
   it.
3. Rename the downloaded file (something like
   `client_secret_{YOUR_CLIENT_ID}.apps.googleusercontent.com`) to
   `google_keys.json`, or whatever the value of `google_key_path` in
   `prefs.json` is.
4. Run `gen_credentials.py`, which will open your default browser, prompting
   you to log in. This generates the second set of OAuth keys, stored in
   `google_credentials.json` (`prefs.google_credential_path`). You’re done!

[gcal]: https://console.cloud.google.com/apis/dashboard
[creds]: https://console.cloud.google.com/apis/credentials
[proj]: https://console.cloud.google.com/projectcreate
[iso8601]: https://en.m.wikipedia.org/wiki/ISO_8601
