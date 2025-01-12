import logging
import configparser
from typing import List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


config = configparser.ConfigParser()
config.read('db_handler/vault/secrets.ini')
api_key = config["Sendgrid"]["api_key"]

class EmailService:
    def __init__(self, recipients: Optional[List[str]] = None,
                 subject: Optional[str] = None,
                 body_text: Optional[str] = None,
                 template_id: Optional[str] = None):
        self.sender = "weekly@ailert.tech"
        self.recipients = recipients if recipients else []
        self.subject = subject if subject else "Weekly Newsletter"
        self.charset = "UTF-8"
        self.body_text = body_text
        self.template_id = template_id

        # Initialize SendGrid client
        try:
            self.sg_client = SendGridAPIClient(api_key=api_key)
        except Exception as e:
            logging.error(f"Failed to initialize SendGrid client: {str(e)}")
            raise

    def _create_mail_object(self, recipient: str) -> Mail:
        """Create a Mail object for a single recipient"""
        from_email = self.sender
        to_email = recipient

        mail = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=self.subject,
            html_content =self.body_text
        )

        # if self.template_id:
        #     mail.template_id = self.template_id
        # else:
        #     content = Content("text/plain", self.body_text)
        #     mail.content = [content]

        return mail

    def send_email(self) -> dict:
        """
        Send emails to all recipients using SendGrid
        Returns:
            dict: Status of email sending operation
        """
        if not self.recipients:
            return {
                "status": "error",
                "message": "No recipients specified",
                "failed_recipients": []
            }

        failed_recipients = []
        successful_count = 0

        for recipient in self.recipients:
            try:
                mail = self._create_mail_object(recipient)
                response = self.sg_client.send(mail)

                if response.status_code in [200, 201, 202]:
                    successful_count += 1
                    logging.info(f"Email sent successfully to {recipient}")
                else:
                    failed_recipients.append({
                        "email": recipient,
                        "error": f"SendGrid API returned status code: {response.status_code}"
                    })
                    logging.error(f"Failed to send email to {recipient}. Status code: {response.status_code}")

            except Exception as e:
                failed_recipients.append({
                    "email": recipient,
                    "error": str(e)
                })
                logging.error(f"Exception while sending email to {recipient}: {str(e)}")

        status = "success" if not failed_recipients else "partial_success" if successful_count else "error"

        return {
            "status": status,
            "message": f"Successfully sent {successful_count} out of {len(self.recipients)} emails",
            "failed_recipients": failed_recipients
        }

    def add_recipient(self, recipient: str) -> None:
        """Add a single recipient to the email list"""
        if recipient not in self.recipients:
            self.recipients.append(recipient)

    def add_recipients(self, recipients: List[str]) -> None:
        """Add multiple recipients to the email list"""
        for recipient in recipients:
            self.add_recipient(recipient)

    def set_template_id(self, template_id: str) -> None:
        """Set the SendGrid template ID"""
        self.template_id = template_id

    def set_body_text(self, body_text: str) -> None:
        """Set the email body text"""
        self.body_text = body_text

    def set_subject(self, subject: str) -> None:
        """Set the email subject"""
        self.subject = subject