"""Email integration package for Shikhor AI."""

from app.integrations.email.sender import (
    get_nid_approval_email_html,
    get_nid_rejection_email_html,
    get_password_reset_otp_html,
    get_rental_accepted_email_html,
    get_rental_rejected_email_html,
    get_rental_request_email_html,
    get_signup_otp_html,
    send_email,
)

__all__ = [
    "send_email",
    "get_signup_otp_html",
    "get_password_reset_otp_html",
    "get_nid_approval_email_html",
    "get_nid_rejection_email_html",
    "get_rental_request_email_html",
    "get_rental_accepted_email_html",
    "get_rental_rejected_email_html",
]
