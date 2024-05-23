import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jinja2 import Environment, FileSystemLoader

from core.config import settings
from fastapi.templating import Jinja2Templates

# from db.models import company

templates = Jinja2Templates(directory="templates/email_templates")

async def send_email_async(email_to, subject, body):
    sender_email = settings.mail_data.USER
    sender_password = settings.mail_data.PASSWORD


    # Create a MIMEText object with email body
    email_body = MIMEText(body, "html")

    # Create a MIMEMultipart object and attach the email body
    email_message = MIMEMultipart()
    email_message["From"] = sender_email
    email_message["To"] = email_to
    email_message["Subject"] = subject
    email_message.attach(email_body)

    try:
        # Connect to SMTP server
        smtp_server = smtplib.SMTP(settings.mail_data.HOST, settings.mail_data.PORT)
        smtp_server.starttls()
        # Login asynchronously
        qwer = await asyncio.get_event_loop().run_in_executor(None, smtp_server.login, sender_email, sender_password)
        print(qwer)
        # Send email asynchronously
        await asyncio.get_event_loop().run_in_executor(None, smtp_server.send_message, email_message)
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    finally:
        # Close SMTP connection
        smtp_server.quit()


async def send_email_with_credentials(email_to: str,  password: str, login: str, username: str | None = None,):
    subject = "Account credentials"
    # body = f"Please verify your email address by clicking the button below:\n\n"
    context = {
        "username": username,
        "login": login,
        "password": password
    }
    # button_html = f'Verification token: {token}'
    env = Environment(loader=FileSystemLoader('templates/email_templates/'))
    template = env.get_template("userCredentials.html")
    body = template.render(context)
    return await send_email_async(email_to, subject, body)


async def send_verification_email(company, token: int):

    subject = "Verify Your Email Address"
    # body = f"Please verify your email address by clicking the button below:\n\n"
    context = {
        "username": company.name,
        "token": token
    }
    # button_html = f'Verification token: {token}'
    env = Environment(loader=FileSystemLoader('templates/email_templates/'))
    template = env.get_template("confirmEmail.html")
    body = template.render(context)
    # body += button_html
    return await send_email_async(company.email, subject, body)


async def forgot_password(username, password: str, email: str):
    from db.models.company import CompanyStore
    subject = "Your new password"

    context = {
        "username": username,
        "password": password
    }
    env = Environment(loader=FileSystemLoader('templates/email_templates/'))
    template = env.get_template("forgotPassword.html")
    body = template.render(context)

    return await send_email_async(email, subject, body)
