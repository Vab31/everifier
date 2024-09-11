from flask import Flask, render_template, request, jsonify
import smtplib
import dns.resolver

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        emails = request.form['emails'].split(',')
        emails = [email.strip() for email in emails if email.strip()]
        results = [verify_email(email) for email in emails]
    return render_template('index.html', results=results)

@app.route('/api/verify', methods=['POST'])
def api_verify():
    data = request.json
    if 'emails' not in data:
        return jsonify({'error': 'No emails provided'}), 400
    
    emails = data['emails']
    if not isinstance(emails, list):
        return jsonify({'error': 'Emails should be a list of strings'}), 400
    
    results = [verify_email(email) for email in emails]
    return jsonify({'results': results})

def verify_email(email):
    try:
        domain = email.split('@')[1]
    except IndexError:
        return f"Invalid email format: {email}"
    
    mx_record = get_mx_record(domain)
    if not mx_record:
        return f"Failed to retrieve MX record for domain: {domain}"
    
    smtp_server = connect_smtp(mx_record)
    if not smtp_server:
        return f"Failed to connect to SMTP server: {mx_record}"
    
    try:
        smtp_server.helo()
        smtp_server.mail('test@example.com')
        code, message = smtp_server.rcpt(email)
        smtp_server.quit()
        if code == 250:
            return f"Email {email} is valid."
        else:
            return f"Email {email} is invalid. Response code: {code}, Message: {message}"
    except Exception as e:
        return f"Error during SMTP transaction for {email}: {e}"

def get_mx_record(domain):
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        return mx_record
    except Exception as e:
        return None

def connect_smtp(mx_record):
    try:
        smtp_server = smtplib.SMTP(mx_record, 25)
        smtp_server.set_debuglevel(1)  # Enable debug output
        return smtp_server
    except Exception as e:
        return None

if __name__ == '__main__':
    app.run(debug=True)
