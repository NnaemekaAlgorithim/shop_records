from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

class CustomActivationEmail:
    html_email_template_name = "email_templates/user_activation.html"

    def __init__(self, context):
        self.context = context

    def send(self, to):
        subject = "Activate Your Owneet Account"
        html_message = render_to_string(self.html_email_template_name, self.context)
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject,
            '', #  Plain text message (not used here)
            from_email,
            to,
            html_message=html_message,
            fail_silently=False,
        )


class BlockedUserEmail:
    html_email_template_name = "email_templates/user_blocked.html"

    def __init__(self, context):
        self.context = context

    def send(self, to):
        subject = "Account Blocked"
        html_message = render_to_string(self.html_email_template_name, self.context)
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject,
            '',  # Plain text message (not used here)
            from_email,
            to,
            html_message=html_message,
            fail_silently=False,
        )


class UnblockedUserEmail:
    html_email_template_name = "email_templates/user_unblocked.html"

    def __init__(self, context):
        self.context = context

    def send(self, to):
        subject = "Account Unblocked"
        html_message = render_to_string(self.html_email_template_name, self.context)
        from_email = settings.DEFAULT_FROM_EMAIL

        send_mail(
            subject,
            '',  # Plain text message (not used here)
            from_email,
            to,
            html_message=html_message,
            fail_silently=False,
        )
