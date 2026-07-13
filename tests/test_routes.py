import db


def _seed_biz():
    db.save_business_info('Test Co', '1 Business Ave', '555-0000')
    db.set_invoice_counter(100)


def _seed_client():
    db.add_client('Client A', '42 Client St', 'Clientville, CA 90000', 'client@example.com')


def _generate(flask_client, **overrides):
    data = {
        'client': 'Client A',
        'invoice_num': '100',
        'address': 'Some notes',
        'work': 'Landscaping',
        'work_price': '500.00',
        'material': 'Mulch',
        'material_price': '75.00',
    }
    data.update(overrides)
    return flask_client.post('/generate', data=data)


# ── Index ──────────────────────────────────────────────────────────────────────

def test_index_redirects_without_biz(client):
    res = client.get('/')
    assert res.status_code == 302
    assert '/setup' in res.location


def test_index_renders_with_biz(client):
    _seed_biz()
    _seed_client()
    res = client.get('/')
    assert res.status_code == 200
    assert b'Client A' in res.data


# ── Setup ──────────────────────────────────────────────────────────────────────

def test_setup_get(client):
    res = client.get('/setup')
    assert res.status_code == 200


def test_setup_post(client):
    res = client.post('/setup', data={
        'company': 'My Co',
        'street': '1 Main St',
        'phone': '555-9999',
        'invoice_start': '50',
    })
    assert res.status_code == 302
    assert db.load_business_info()['company'] == 'My Co'
    assert db.load_invoice_counter() == '50'


# ── Client CRUD ────────────────────────────────────────────────────────────────

def test_add_client(client):
    _seed_biz()
    res = client.post('/add-client', data={
        'name': 'New Client',
        'street': '5 New St',
        'city_state_zip': 'Newtown, NY 10001',
        'email': 'new@example.com',
    })
    assert res.status_code == 302
    assert len(db.get_clients()) == 1


def test_edit_client(client):
    _seed_biz()
    _seed_client()
    res = client.post('/edit-client', data={
        'original_name': 'Client A',
        'name': 'Client B',
        'street': '99 B St',
        'city_state_zip': 'B City, TX 75000',
        'email': 'b@example.com',
    })
    assert res.status_code == 302
    assert db.get_clients()[0].name == 'Client B'


def test_delete_client(client):
    _seed_biz()
    _seed_client()
    res = client.post('/delete-client', data={'name': 'Client A'})
    assert res.status_code == 302
    assert db.get_clients() == []


# ── Generate / Preview / PDF ───────────────────────────────────────────────────

def test_generate_returns_token(client):
    _seed_biz()
    _seed_client()
    res = _generate(client)
    assert res.status_code == 200
    assert 'token' in res.get_json()


def test_view_preview(client):
    _seed_biz()
    _seed_client()
    token = _generate(client).get_json()['token']
    res = client.get(f'/view/{token}')
    assert res.status_code == 200
    assert b'invoice #100.pdf' in res.data


def test_serve_pdf(client):
    _seed_biz()
    _seed_client()
    token = _generate(client).get_json()['token']
    res = client.get(f'/pdf/{token}')
    assert res.status_code == 200
    assert res.content_type == 'application/pdf'
    assert res.data[:4] == b'%PDF'


def test_view_invalid_token_redirects(client):
    res = client.get('/view/nonexistent')
    assert res.status_code == 302


def test_pdf_invalid_token(client):
    res = client.get('/pdf/nonexistent')
    assert res.status_code == 404


# ── Download ───────────────────────────────────────────────────────────────────

def test_download_increments_counter(client):
    _seed_biz()
    _seed_client()
    db.set_invoice_counter(5)
    token = _generate(client, invoice_num='5').get_json()['token']

    client.get(f'/download/{token}')
    assert db.load_invoice_counter() == '6'


def test_download_does_not_double_increment(client):
    _seed_biz()
    _seed_client()
    db.set_invoice_counter(5)
    token = _generate(client, invoice_num='5').get_json()['token']

    client.get(f'/download/{token}')
    client.get(f'/download/{token}')
    assert db.load_invoice_counter() == '6'


# ── Error cases ────────────────────────────────────────────────────────────────

def test_generate_unknown_client(client):
    _seed_biz()
    _seed_client()
    res = _generate(client, client='Nobody')
    assert res.status_code == 400


def test_generate_invalid_price(client):
    _seed_biz()
    _seed_client()
    res = _generate(client, work_price='not-a-number')
    assert res.status_code == 400
