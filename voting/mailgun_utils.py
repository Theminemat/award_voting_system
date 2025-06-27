import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_mailgun_template_email(to_email, subject, template_name, template_variables):
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN or not settings.MAILGUN_API_URL:
        logger.error("Mailgun API key, domain, or URL not configured in settings.")
        return False

    try:
        response = requests.post(
            settings.MAILGUN_API_URL,
            auth=("api", settings.MAILGUN_API_KEY),
            data={
                "from": settings.MAILGUN_SENDER_EMAIL,
                "to": to_email,
                "subject": subject,
                "template": template_name,
                "h:X-Mailgun-Variables": json.dumps(template_variables)
            }
        )
        response.raise_for_status()
        logger.info(f"Mailgun email sent successfully to {to_email}. Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Mailgun email to {to_email}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Mailgun API Error Response: {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending Mailgun email to {to_email}: {e}")
        return False
