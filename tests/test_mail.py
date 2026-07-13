import pytest
from unittest.mock import patch, MagicMock
from mail import send_invoice


_BIZ = {'company': 'Test Co', 'street': '1 Main', 'phone': '555-0000'}
_PDF = b'%PDF-1.4 fake content'


def test_send_invoice_missing_credentials(monkeypatch):
    monkeypatch.delenv('EMAIL_USER', raising=False)
    monkeypatch.delenv('EMAIL_PASS', raising=False)
    with pytest.raises(RuntimeError, match='EMAIL_USER and EMAIL_PASS'):
        send_invoice('to@example.com', 'invoice.pdf', _PDF, _BIZ, '42')


def test_send_invoice_missing_user(monkeypatch):
    monkeypatch.delenv('EMAIL_USER', raising=False)
    monkeypatch.setenv('EMAIL_PASS', 'pass')
    with pytest.raises(RuntimeError):
        send_invoice('to@example.com', 'invoice.pdf', _PDF, _BIZ, '42')


def test_send_invoice_missing_password(monkeypatch):
    monkeypatch.setenv('EMAIL_USER', 'from@gmail.com')
    monkeypatch.delenv('EMAIL_PASS', raising=False)
    with pytest.raises(RuntimeError):
        send_invoice('to@example.com', 'invoice.pdf', _PDF, _BIZ, '42')


def test_send_invoice_calls_smtp(monkeypatch):
    monkeypatch.setenv('EMAIL_USER', 'from@gmail.com')
    monkeypatch.setenv('EMAIL_PASS', 'app-password')

    mock_instance = MagicMock()
    mock_smtp = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_instance)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    with patch('mail.smtplib.SMTP_SSL', mock_smtp):
        send_invoice('client@example.com', 'invoice #42.pdf', _PDF, _BIZ, '42')

    mock_smtp.assert_called_once_with('smtp.gmail.com', 465)
    mock_instance.login.assert_called_once_with('from@gmail.com', 'app-password')
    mock_instance.send_message.assert_called_once()
