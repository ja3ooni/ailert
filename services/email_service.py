import boto3
from botocore.exceptions import ClientError

class EmailService:
    def __init__(self, recipients=None, subject=None, body_text=None, template_id=None):
        self.sender = "weekly@ailert.tech"
        self.recipients = recipients
        self.configuration_set = "ConfigSet"
        self.aws_region = "us-east-1"
        self.subject = subject if subject else "Weekly Newsletter"
        self.charset = "UTF-8"
        self.body_text = body_text
        self.template_id = template_id

    def _get_newsletter_content(self) -> str:
        try:
            with open('generated_newsletter.html', 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            raise Exception("Newsletter file not found. Please ensure the file exists.")
        except Exception as e:
            raise Exception(f"Error reading newsletter file: {str(e)}")

# The HTML body of the email.
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test (SDK for Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://aws.amazon.com/sdk-for-python/'>
      AWS SDK for Python (Boto)</a>.</p>
</body>
</html>
            """


client = boto3.client('ses', region_name=AWS_REGION)
try:
    response = client.send_email(
        Destination={
            'ToAddresses': [
                RECIPIENT,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': CHARSET,
                    'Data': BODY_HTML,
                },
                # 'Text': {
                #     'Charset': CHARSET,
                #     'Data': BODY_TEXT,
                # },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
        },
        Source=SENDER,
        ConfigurationSetName=CONFIGURATION_SET,
    )

except ClientError as e:
    print(e.response['Error']['Message'])
else:
    print("Email sent! Message ID:"),
    print(response['MessageId'])