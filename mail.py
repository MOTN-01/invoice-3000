import os
import smtplib
from email.message import EmailMessage


def send_invoice(to_email, filename, pdf_bytes, biz, invoice_num, cc_emails=None, message=''):
    user = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASS')
    if not user or not password:
        raise RuntimeError('EMAIL_USER and EMAIL_PASS are not set in .env')

    msg = EmailMessage()
    msg['From'] = user
    msg['To'] = to_email
    if cc_emails:
        msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = f'Invoice #{invoice_num} from {biz["company"]}'
    note = f'{message}\n\n' if message else ''
    msg.set_content(
        f'Hi,\n\n{note}Please find attached invoice #{invoice_num}.\n\n'
        f'Thank you,\n{biz["company"]}'
    )
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=filename)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
