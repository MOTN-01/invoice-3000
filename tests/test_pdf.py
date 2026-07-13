from db import Client
from pdf import generate_invoice


def _client():
    return Client('Test Corp', '1 Main St', 'Springfield, IL 62701', 'test@example.com')


def _biz():
    return {'company': 'My Biz', 'street': '100 Biz Blvd', 'phone': '555-1234'}


def test_generate_invoice_returns_pdf():
    buf = generate_invoice(_client(), 'Some notes', 'Mowing lawns', '300.00',
                           '42', 'Grass seed', '50.00', _biz())
    assert buf.read(4) == b'%PDF'


def test_generate_invoice_zero_material():
    buf = generate_invoice(_client(), '', 'Hedge trimming', '150.00',
                           '43', 'None', '0', _biz())
    assert buf.read(4) == b'%PDF'


def test_generate_invoice_special_chars():
    buf = generate_invoice(
        _client(),
        'Notes with <tags> & "quotes"',
        'Work with <special> chars & symbols',
        '100.00', '44',
        'Materials & more <items>',
        '25.00', _biz(),
    )
    assert buf.read(4) == b'%PDF'
