from db import (
    get_clients, get_client_email, add_client, update_client, delete_client,
    load_business_info, save_business_info,
    load_invoice_counter, set_invoice_counter, increment_invoice_counter,
)


def test_get_clients_empty():
    assert get_clients() == []


def test_add_and_get_clients():
    add_client('ACME Corp', '123 Main St', 'Springfield, IL 62701', 'acme@example.com')
    clients = get_clients()
    assert len(clients) == 1
    c = clients[0]
    assert c.name == 'ACME Corp'
    assert c.street == '123 Main St'
    assert c.city_state_zip == 'Springfield, IL 62701'
    assert c.email == 'acme@example.com'


def test_add_client_duplicate_ignored():
    add_client('Dupe', '1 St', 'City, ST 00000')
    add_client('Dupe', '2 Ave', 'Town, ST 11111')
    assert len(get_clients()) == 1


def test_add_client_no_email():
    add_client('NoEmail', '1 St', 'City, ST 00000')
    assert get_clients()[0].email == ''


def test_update_client():
    add_client('Old Name', '1 St', 'City, ST 00000', 'old@example.com')
    update_client('Old Name', 'New Name', '2 Ave', 'Town, ST 11111', 'new@example.com')
    clients = get_clients()
    assert len(clients) == 1
    c = clients[0]
    assert c.name == 'New Name'
    assert c.street == '2 Ave'
    assert c.city_state_zip == 'Town, ST 11111'
    assert c.email == 'new@example.com'


def test_delete_client():
    add_client('ToDelete', '1 St', 'City, ST 00000')
    delete_client('ToDelete')
    assert get_clients() == []


def test_get_client_email():
    add_client('Emailer', '1 St', 'City, ST 00000', 'test@example.com')
    assert get_client_email('Emailer') == 'test@example.com'


def test_get_client_email_no_email_stored():
    add_client('NoEmail', '1 St', 'City, ST 00000')
    assert get_client_email('NoEmail') is None


def test_get_client_email_nonexistent():
    assert get_client_email('Ghost') is None


def test_load_business_info_empty():
    assert load_business_info() is None


def test_save_and_load_business_info():
    save_business_info('My Co', '100 Biz Blvd', '555-1234')
    biz = load_business_info()
    assert biz == {'company': 'My Co', 'street': '100 Biz Blvd', 'phone': '555-1234'}


def test_invoice_counter_default():
    assert load_invoice_counter() == '1'


def test_set_invoice_counter():
    set_invoice_counter(42)
    assert load_invoice_counter() == '42'


def test_increment_invoice_counter():
    set_invoice_counter(10)
    increment_invoice_counter()
    assert load_invoice_counter() == '11'
