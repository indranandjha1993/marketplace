from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    subject = f'Order Confirmation #{order.order_number}'

    # Render email content from template
    html_content = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'items': order.items.all(),
    })

    # Plain text version
    text_content = strip_tags(html_content)

    # Create email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email]
    )

    # Attach HTML version
    email.attach_alternative(html_content, "text/html")

    # Send email
    email.send()


def send_order_status_update_email(order, status):
    """Send order status update email to customer."""
    subject = f'Order #{order.order_number} Status Update'

    # Render email content from template
    html_content = render_to_string('emails/order_status_update.html', {
        'order': order,
        'status': status,
    })

    # Plain text version
    text_content = strip_tags(html_content)

    # Create and send email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()
