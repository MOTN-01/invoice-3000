from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from io import BytesIO
import uuid
import json
from dotenv import load_dotenv
from db import (init_db, get_clients, get_client_email, get_client_cc_emails,
                add_client as db_add_client, update_client, delete_client,
                load_business_info, save_business_info,
                load_invoice_counter, set_invoice_counter, increment_invoice_counter)
from pdf import generate_invoice
from mail import send_invoice

load_dotenv()

app = Flask(__name__)
init_db()

# token -> {'data', 'filename', 'invoice_num', 'client_name', 'committed'}
_pending = {}


@app.context_processor
def inject_globals():
    return {'biz': load_business_info()}


@app.route('/')
def index():
    if not load_business_info():
        return redirect(url_for('setup'))
    clients = get_clients()
    clients_json = json.dumps([
        {'name': c.name, 'street': c.street,
         'city_state_zip': c.city_state_zip, 'email': c.email,
         'cc_emails': c.cc_emails}
        for c in clients
    ])
    return render_template('index.html',
                           clients=clients,
                           clients_json=clients_json,
                           selected_client=request.args.get('client', ''),
                           invoice_num=load_invoice_counter())


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        save_business_info(request.form['company'],
                           request.form['street'],
                           request.form['phone'])
        set_invoice_counter(request.form['invoice_start'])
        return redirect(url_for('index'))
    return render_template('setup.html')


@app.route('/edit-business', methods=['POST'])
def edit_business():
    save_business_info(request.form['company'],
                       request.form['street'],
                       request.form['phone'])
    set_invoice_counter(request.form['invoice_num'])
    return redirect(url_for('index'))


def _cc_emails_from_form():
    return ','.join(e.strip() for e in request.form.getlist('cc_emails') if e.strip())


@app.route('/add-client', methods=['POST'])
def add_client():
    name = request.form['name']
    db_add_client(name, request.form.get('street', ''),
                  request.form.get('city_state_zip', ''),
                  request.form.get('email', ''),
                  _cc_emails_from_form())
    return redirect(url_for('index', client=name))


@app.route('/edit-client', methods=['POST'])
def edit_client():
    update_client(request.form['original_name'],
                  request.form['name'],
                  request.form.get('street', ''),
                  request.form.get('city_state_zip', ''),
                  request.form.get('email', ''),
                  _cc_emails_from_form())
    return redirect(url_for('index', client=request.form['name']))


@app.route('/delete-client', methods=['POST'])
def delete_client_route():
    delete_client(request.form['name'])
    return redirect(url_for('index'))


@app.route('/generate', methods=['POST'])
def generate():
    clients = get_clients()
    selected = request.form.get('client')
    client = next((c for c in clients if c.name == selected), None)
    if not client:
        return 'No client selected', 400

    try:
        work_price = str(float(request.form.get('work_price') or 0))
        material_price = str(float(request.form.get('material_price') or 0))
    except ValueError:
        return 'Prices must be numbers', 400

    invoice_num = request.form['invoice_num']
    biz = load_business_info()

    pdf_buf = generate_invoice(
        client,
        request.form['address'],
        request.form['work'],
        work_price,
        invoice_num,
        request.form.get('material', ''),
        material_price,
        biz
    )

    token = uuid.uuid4().hex
    pdf_buf.seek(0)
    _pending[token] = {
        'data': pdf_buf.read(),
        'filename': f'invoice #{invoice_num}.pdf',
        'invoice_num': invoice_num,
        'client_name': selected,
        'committed': False,
    }

    return jsonify(token=token)


@app.route('/view/<token>')
def view_preview(token):
    if token not in _pending:
        return redirect(url_for('index'))
    entry = _pending[token]
    client_email = get_client_email(entry['client_name'])
    client_cc_emails = get_client_cc_emails(entry['client_name'])
    return render_template('preview.html', token=token,
                           filename=entry['filename'],
                           client_email=client_email,
                           client_cc_emails=client_cc_emails)


@app.route('/pdf/<token>')
def serve_pdf(token):
    if token not in _pending:
        return 'Not found', 404
    entry = _pending[token]
    return send_file(BytesIO(entry['data']), mimetype='application/pdf',
                     as_attachment=False, download_name=entry['filename'])


@app.route('/download/<token>')
def download(token):
    if token not in _pending:
        return 'Not found', 404
    entry = _pending[token]
    if not entry['committed']:
        increment_invoice_counter()
        entry['committed'] = True
    return send_file(BytesIO(entry['data']), mimetype='application/pdf',
                     as_attachment=True, download_name=entry['filename'])


@app.route('/email/<token>', methods=['POST'])
def email_invoice(token):
    if token not in _pending:
        return 'Not found', 404
    entry = _pending[token]
    client_email = get_client_email(entry['client_name'])
    if not client_email:
        return f'No email on file for {entry["client_name"]}', 400
    try:
        biz = load_business_info()
        payload = request.get_json(silent=True) or {}
        to_email = (payload.get('to_email') or '').strip() or client_email
        cc_emails = [e.strip() for e in payload.get('cc_emails', []) if e and e.strip()]
        message = (payload.get('message') or '').strip()
        send_invoice(to_email, entry['filename'], entry['data'], biz,
                     entry['invoice_num'], cc_emails, message)
        if not entry['committed']:
            increment_invoice_counter()
            entry['committed'] = True
        return jsonify(ok=True, email=to_email)
    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
