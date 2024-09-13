import os
import aiosmtplib  # Asynchronous SMTP library
import dns.asyncresolver  # Asynchronous DNS resolver from dnspython
import logging
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import asyncio

app = Flask(__name__)

# Rate limiting setup to prevent abuse (e.g., too many API requests per user)
limiter = Limiter(get_remote_address, app=app)

# Basic logging configuration
logging.basicConfig(level=logging.INFO)

# Get the sender email from environment variables, defaulting to a test email
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'test@example.com')

# API endpoint for email verification
@app.route('/api/verify', methods=['POST'])
@limiter.limit("32 per minute")
async def api_verify():
    data = request.json
    if 'emails' not in data:
        return jsonify({'error': 'No emails provided'}), 400
    
    emails = data['emails']
    if not isinstance(emails, list):
        return jsonify({'error': 'Emails should be a list of strings'}), 400
    
    # Gather results asynchronously
    results = await asyncio.gather(*(verify_email(email) for email in emails))
    return jsonify({'results': results})

# Asynchronous email verification function
async def verify_email(email):
    try:
        # Extract domain from email
        domain = email.split('@')[1]
    except IndexError:
        return f"Invalid email format: {email}"
    
    # Get MX record asynchronously
    mx_record = await get_mx_record(domain)
    if not mx_record:
        return f"Failed to retrieve MX record for domain: {domain}"
    
    # Connect to SMTP server asynchronously
    smtp_server = await connect_smtp(mx_record)
    if not smtp_server:
        return f"Failed to connect to SMTP server: {mx_record}"
    
    try:
        # Asynchronous SMTP transaction
        await smtp_server.ehlo()
        await smtp_server.mail(SENDER_EMAIL)
        code, message = await smtp_server.rcpt(email)
        await smtp_server.quit()
        
        if code == 250:
            return f"Email {email} is valid."
        else:
            return f"Email {email} is invalid. Response code: {code}, Message: {message}"
    except Exception as e:
        logging.error(f"Error during SMTP transaction for {email}: {e}")
        return f"Error during SMTP transaction for {email}: {e}"

# Asynchronous function to get MX record
async def get_mx_record(domain):
    try:
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        # Asynchronously resolve the MX record
        records = await resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        return mx_record
    except Exception as e:
        logging.error(f"DNS lookup failed for domain {domain}: {e}")
        return None

# Asynchronous function to connect to the SMTP server
async def connect_smtp(mx_record):
    try:
        # Asynchronously connect to the SMTP server using aiosmtplib
        smtp_server = aiosmtplib.SMTP(hostname=mx_record, port=25, timeout=10)
        await smtp_server.connect()
        await smtp_server.starttls()
        return smtp_server
    except Exception as e:
        logging.error(f"Failed to connect securely to SMTP server: {e}")
        return None

if __name__ == '__main__':
    # Run the Flask app asynchronously with debug off
    app.run(debug=False, host='0.0.0.0')




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

