import os
import smtplib  # For synchronous SMTP
import dns.resolver  # For DNS resolution
import logging
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Rate limiting setup to prevent abuse (e.g., too many API requests per user)
limiter = Limiter(get_remote_address, app=app)

# Basic logging configuration
logging.basicConfig(level=logging.INFO)

# Get the sender email from environment variables, defaulting to a test email
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'test@example.com')

# API endpoint for email verification
@app.route('/api/verify', methods=['POST'])
@limiter.limit("10 per minute")
def api_verify():
    data = request.json
    if 'emails' not in data:
        return jsonify({'error': 'No emails provided'}), 400
    
    emails = data['emails']
    if not isinstance(emails, list):
        return jsonify({'error': 'Emails should be a list of strings'}), 400

    # Process email verification synchronously
    results = [verify_email(email) for email in emails]
    return jsonify({'results': results})

# Synchronous email verification function
def verify_email(email):
    try:
        # Extract domain from email
        domain = email.split('@')[1]
    except IndexError:
        return f"Invalid email format: {email}"
    
    # Get MX record
    mx_record = get_mx_record(domain)
    if not mx_record:
        return f"Failed to retrieve MX record for domain: {domain}"

    # Connect to SMTP server synchronously
    smtp_server = connect_smtp(mx_record)
    if not smtp_server:
        return f"Failed to connect to SMTP server: {mx_record}"

    try:
        # Synchronous SMTP transaction
        smtp_server.ehlo()
        smtp_server.mail(SENDER_EMAIL)
        code, message = smtp_server.rcpt(email)
        smtp_server.quit()

        if code == 250:
            return f"Email {email} is valid."
        else:
            return f"Email {email} is invalid. Response code: {code}, Message: {message}"
    except Exception as e:
        logging.error(f"Error during SMTP transaction for {email}: {e}")
        return f"Error during SMTP transaction for {email}: {e}"

# Synchronous function to get MX record
def get_mx_record(domain):
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        # Synchronously resolve the MX record
        records = resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        return mx_record
    except Exception as e:
        logging.error(f"DNS lookup failed for domain {domain}: {e}")
        return None

# Synchronous function to connect to the SMTP server
def connect_smtp(mx_record):
    try:
        # Synchronously connect to the SMTP server
        smtp_server = smtplib.SMTP(host=mx_record, port=25, timeout=10)
        smtp_server.starttls()  # Using TLS for encryption
        return smtp_server
    except Exception as e:
        logging.error(f"Failed to connect securely to SMTP server: {e}")
        return None

if __name__ == '__main__':
    # Run the Flask app synchronously with debug off
    app.run(debug=False, host='0.0.0.0',)



# from flask import Flask, render_template, request, jsonify
# import smtplib
# import dns.resolver

# app = Flask(__name__)

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     results = []
#     if request.method == 'POST':
#         emails = request.form['emails'].split(',')
#         emails = [email.strip() for email in emails if email.strip()]
#         results = [verify_email(email) for email in emails]
#     return render_template('index.html', results=results)

# @app.route('/api/verify', methods=['POST'])
# def api_verify():
#     data = request.json
#     if 'emails' not in data:
#         return jsonify({'error': 'No emails provided'}), 400
    
#     emails = data['emails']
#     if not isinstance(emails, list):
#         return jsonify({'error': 'Emails should be a list of strings'}), 400
    
#     results = [verify_email(email) for email in emails]
#     return jsonify({'results': results})

# def verify_email(email):
#     try:
#         domain = email.split('@')[1]
#     except IndexError:
#         return f"Invalid email format: {email}"
    
#     mx_record = get_mx_record(domain)
#     if not mx_record:
#         return f"Failed to retrieve MX record for domain: {domain}"
    
#     smtp_server = connect_smtp(mx_record)
#     if not smtp_server:
#         return f"Failed to connect to SMTP server: {mx_record}"
    
#     try:
#         smtp_server.helo()
#         smtp_server.mail('test@example.com')
#         code, message = smtp_server.rcpt(email)
#         smtp_server.quit()
#         if code == 250:
#             return f"Email {email} is valid."
#         else:
#             return f"Email {email} is invalid. Response code: {code}, Message: {message}"
#     except Exception as e:
#         return f"Error during SMTP transaction for {email}: {e}"

# def get_mx_record(domain):
#     try:
#         records = dns.resolver.resolve(domain, 'MX')
#         mx_record = str(records[0].exchange)
#         return mx_record
#     except Exception as e:
#         return None

# def connect_smtp(mx_record):
#     try:
#         smtp_server = smtplib.SMTP(mx_record, 25)
#         smtp_server.set_debuglevel(1)  # Enable debug output
#         return smtp_server
#     except Exception as e:
#         return None

# if __name__ == '__main__':
#     app.run(debug=True)

