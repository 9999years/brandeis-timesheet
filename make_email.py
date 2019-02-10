from email import message
from datetime import datetime

from decouple import config

import timesheet


def make(during: datetime = None) -> message.EmailMessage:
    start, end = timesheet.work_week(during)
    start_date = start.date().isoformat()
    end_date = end.date().isoformat()
    msg = message.EmailMessage()

    # message body
    msg['Subject'] = config('EMAIL_SUBJECT').format(start_date)
    msg['From'] = config('EMAIL_FROM')
    msg['To'] = config('EMAIL_TO')
    cc = config('EMAIL_CC', default='')
    if cc:
        msg['Cc'] = cc
    msg.set_content(config('EMAIL_BODY').format(start_date, end_date).replace('\\n', '\n'))

    msg.make_mixed()
    with open(config('PDF_FILENAME'), mode='rb') as f:
        msg.add_attachment(f.read(),
                           maintype='application',
                           subtype='pdf',
                           filename=config('PDF_FILENAME'.format(start_date)))

    return msg


def main():
    print(str(make()))


if __name__ == '__main__':
    main()
