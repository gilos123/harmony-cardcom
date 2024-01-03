from flask import Flask, request, jsonify
from flask_cors import CORS
import ssl
from werkzeug.serving import run_simple
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
from datetime import date
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email settings
to_email = "gil8461@gmail.com"
from_email = "gil8461@gmail.com"  # Replace with your email address
subject = "salesforce-cardcom"
password = "google@8461"
# Create the email message
msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = subject

smtp_server = 'smtp.gmail.com'
port = 587

def sf_api_call(action, parameters={}, method='get', data={}, access_token1='', instance_url1=''):
    """
    Helper function to make calls to Salesforce REST API.
    Parameters: action (the URL), URL params, method (get, post or patch), data for POST/PATCH.
    """
    headers = {
        'Content-type': 'application/json',
        'Accept-Encoding': 'gzip',
        'Authorization': 'Bearer %s' % access_token1
    }
    if method == 'get':
        r = requests.request(method, instance_url1 + action, headers=headers, params=parameters, timeout=30)
    elif method in ['post', 'patch']:
        r = requests.request(method, instance_url1 + action, headers=headers, json=data, params=parameters, timeout=10)
    else:
        # other methods not implemented in this example
        raise ValueError('Method should be get or post or patch.')
    print('Debug: API %s call: %s' % (method, r.url))
    if r.status_code < 300:
        if method == 'patch':
            return None
        else:
            return r.json()
    else:
        raise Exception('API error when calling %s : %s' % (r.url, r.content))


today_date = str(date.today())

app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# Load your private key and certificate
context.load_cert_chain(r'C:\Certbot\live\giltwi.ddns.net-0001\fullchain.pem',
                        r'C:\Certbot\live\giltwi.ddns.net-0001\privkey.pem')

# Optional: Set up ciphers
ciphers = (
    'DHE-RSA-AES256-GCM-SHA384:'
    'DHE-RSA-AES128-GCM-SHA256:'
    'ECDHE-ECDSA-AES256-GCM-SHA384:'
    'ECDHE-ECDSA-AES128-GCM-SHA256'
)
context.set_ciphers(ciphers)

# Disable older protocols
context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1



@app.route('/home', methods=['GET'])
def home():
    return "Hello, this is the home page."


@app.route('/receive_get', methods=['GET'])
def receive_get():
    # You can access the query parameters with request.args
    print('goo')
    param = request.args.get('suminfull')
    print(param)
    return jsonify({"message": "Data received", "data": param})


@app.route('/<customer>', methods=["POST"])
def receive_post_now(customer):
    params2 = ''


    with open('data.json', 'r') as f:
        file = json.load(f)
        params2 = file[customer]['params']
        print(params2)

        print('got it')
        data_cardcom = request.form
        r = requests.post("https://login.salesforce.com/services/oauth2/token", params=params2)
        print(r.text)
        # if you connect to a Sandbox, use test.salesforce.com instead
        access_token = r.json().get("access_token")
        instance_url = r.json().get("instance_url")
        print("Access Token:", access_token)
        print("Instance URL", instance_url)
        data_salesforce = {
            "Date__c": today_date,
            "DocNum__c": data_cardcom['invNumber'],
            "DocType__c": data_cardcom['invType'],
            "Currency__c": data_cardcom['cointype'],
            "FullName__c": data_cardcom['CardOwnerName'],
            "Email__c": data_cardcom['UserEmail'],
            "BusinessID__c": data_cardcom['invCompanyID'],
            "City__c": data_cardcom['intCity'],
            "Address1__c": data_cardcom['InvAddress'],
            "Address2__c": data_cardcom['InvAddress2'],
            "Mobile__c": data_cardcom['InvMobile'],
            "Phone__c": data_cardcom['InvPhone'],
            "TotalAmount__c": data_cardcom['suminfull']
        }
        print('/services/data/v59.0/sobjects/Cardcom__c/')
        print(data_salesforce)
        call = sf_api_call('/services/data/v59.0/sobjects/Cardcom__c/', method="post", data=data_salesforce,
                           access_token1=access_token, instance_url1=instance_url)

        opportunity_id = call.get('id')
        print(opportunity_id)
        if r.status_code > 300:
            body = r.text
            msg.attach(MIMEText(body, 'plain'))
            try:
                server = smtplib.SMTP(smtp_server, port)
                server.starttls()  # Secure the connection
                server.login(from_email, password)  # Login to the server
                server.sendmail(from_email, to_email, msg.as_string())  # Send the email
                print("Email sent successfully!")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                server.quit()
    # Send a response
        return jsonify({"message": "Data received", "data": data_cardcom})



if __name__ == '__main__':
    run_simple('0.0.0.0', 80, app, ssl_context=context)
