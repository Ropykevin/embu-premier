from unittest.mock import patch

from app.services import email_service


def test_contact_notification(app):
    with app.app_context():
        from app.models import ContactMessage

        message = ContactMessage(
            full_name="Jane Doe",
            phone="+254700000001",
            email="jane@example.com",
            subject="Inquiry",
            message="Hello clinic",
        )

        with patch.object(email_service, "_send_email", return_value=True) as mock_send:
            result = email_service.notify_new_contact_message(message)

        assert result is True
        mock_send.assert_called_once()
        assert "contact message" in mock_send.call_args[0][0].lower()
