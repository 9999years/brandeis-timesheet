from email.mime import application, text, audio, image, message
from email import message, mime
from datetime import datetime
import os
import mimetypes
from typing import Dict, Any
import base64
from argparse import ArgumentParser

from decouple import config

import timesheet
import creds

MIME_CLASSES = {
    'text': mime.text.MIMEText,
    'application': mime.application.MIMEApplication,
    'audio': mime.audio.MIMEAudio,
    'image': mime.image.MIMEImage,
    'message': mime.message.MIMEMessage,
}

def _make(
        sender: str,
        to: str,
        subject: str,
        message_text: str,
        fname: str,
        cc: str = None,
        mime_filename: str = None) -> mime.base.MIMEBase:
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      cc: People to cc, ignored if falsey
      fname: The path to the file to be attached.
      mime_filename: Filename of attachment in email; set to file's basename if
        omitted

    Returns:
      An object containing a base64url encoded email object.
    """
    message = mime.multipart.MIMEMultipart()
    message['To'] = to
    message['Subject'] = subject

    if sender:
        message['From'] = sender

    if cc:
        message['Cc'] = cc

    msg = mime.text.MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(fname)
    if content_type is None or encoding is not None:
      content_type = 'application/octet-stream'

    main_type, sub_type = content_type.split('/', 1)
    with open(fname, 'rb') as fp:
        if main_type in MIME_CLASSES:
            msg = MIME_CLASSES[main_type](fp.read(), _subtype=sub_type)
        else:
            msg = mime.base.MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())

    if mime_filename is None:
        mime_filename = os.path.basename(fname)
    msg.add_header('Content-Disposition', 'attachment', filename=mime_filename)
    message.attach(msg)

    return message


def convert_gmail(msg: mime.base.MIMEBase) -> Dict[str, Any]:
  return {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')}


def make(during: datetime = None) -> message.EmailMessage:
    start, end = timesheet.work_week(during)
    start_date = start.date().isoformat()
    end_date = end.date().isoformat()

    return _make(
            sender        = config('EMAIL_FROM'),
            to            = config('EMAIL_TO'),
            subject       = config('EMAIL_SUBJECT').format(start_date),
            message_text  = config('EMAIL_BODY')
                                .format(start_date, end_date)
                                .replace('\\n', '\n'),
            fname         = config('PDF_FILENAME'),
            cc            = config('EMAIL_CC', default=''),
            mime_filename = config('EMAIL_ATTACHMENT_NAME').format(start_date),
            )

def send_message(message: mime.base.MIMEBase, service = None, user_id: str = 'me') -> Dict[str, Any]:
    """Send an email message.

    Args:
      message: Message to be sent.
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.

    Returns:
      Sent Message.
    """
    if service is None:
        service = creds.build_gmail()
    return (service.users()
                .messages()
                .send(userId=user_id, body=convert_gmail(message))
                .execute())


def argparser() -> ArgumentParser():
    parser = ArgumentParser()
    parser.add_argument('-s', '--send', action='store_true', help='Actually send the email')
    return parser


def main():
    args = argparser().parse_args()
    msg = make()
    if args.send:
        print(send_message(msg))
    else:
        print('Headers:')
        for h, v in msg.items():
            print(h + ':', v)
        print('Data:')
        for part in msg.get_payload():
            print('-------------------------------')
            if isinstance(part, mime.text.MIMEText):
                print(part.as_string())
            else:
                for h, v in part.items():
                    print(h + ':', v)



if __name__ == '__main__':
    main()
