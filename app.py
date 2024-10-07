import os
from flask import Flask, request, jsonify, redirect, session
from onelogin.saml2.auth import OneLogin_Saml2_Auth

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace this with a secure key in production
# Configuration for SAML
SAML_PATH = os.path.join(os.getcwd(), 'saml')

@app.route('/')
def say_hi():
    return 'Hi! This is the addition service.'

def init_saml_auth(req):
    print('In init auth')
    auth = OneLogin_Saml2_Auth(req, custom_base_path=SAML_PATH)
    return auth

def prepare_flask_request(request):
    print('In Prepare Flask')
    url_data = request.url.split('?')
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'script_name': request.path,
        'server_port': request.host.split(':')[1] if ':' in request.host else '80',
        'get_data': request.args.copy(),
        'post_data': request.form.copy(),
    }


@app.route('/saml/login')
def login():
    print('In SAML Login')
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    return redirect(auth.login())

@app.route('/saml/callback', methods=['POST'])
def login_callback():
    req = prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()

    if not errors:
        session['samlUserdata'] = auth.get_attributes()
        session['samlNameId'] = auth.get_nameid()
        print(session['samlUserdata'])
        name_ = session['samlUserdata']['http://schemas.microsoft.com/identity/claims/displayname']
        #return redirect(url_for('index'))
        return f"{name_} User authenticated!"
    else:
        return f"Error in SAML Authentication: {errors}", 500
        
if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)