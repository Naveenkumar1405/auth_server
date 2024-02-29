from flask import Flask, request, redirect, render_template, jsonify
from urllib.parse import parse_qs
import pyrebase, secrets, string

app = Flask(__name__)

Config = {"apiKey": "AIzaSyC2psok5Y20qJvtXjiPZEDQYbGkitdwk0M", "authDomain": "smart-things-ab7d2.firebaseapp.com","databaseURL": "https://smart-things-ab7d2-default-rtdb.firebaseio.com", "projectId": "smart-things-ab7d2", "storageBucket": "smart-things-ab7d2.appspot.com", "messagingSenderId": "928008787147","appId": "1:928008787147:web:a4e37aca5a8a4fb186b74e"}

firebase = pyrebase.initialize_app(Config)
db = firebase.database()
auth = firebase.auth()

CLIENT_ID = "c513e16bfad60ed5"
CLIENT_SECRET = "lNxtrRja7W9CtpYT8objV4aA4gxZcJvHyV6bwwZsuf3G"

@app.route('/login', methods=['GET'])
def login():
    state = request.args.get("state")
    redirect_uri = request.args.get("redirect_uri")
    return render_template("login.html", state=state, redirect_uri=redirect_uri)

@app.route('/login-auth', methods=['POST'])
def login_auth():
    email = request.form.get("email")
    password = request.form.get("password")
    state = request.form.get("state")
    redirect_uri = request.form.get("redirect_uri")
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        uid = user['localId']
        authorization_code = generate_authorization_code(uid)
        redirect_uri_final = f"{redirect_uri}?state={state}&code={authorization_code}"
        return redirect(redirect_uri_final)
    except Exception as e:
        return render_template("login.html", message="Invalid username and password", state=state, redirect_uri=redirect_uri)

@app.route('/accesstoken', methods=['POST'])
def accessTokens():
    raw_data = request.get_data()
    parsed_data = parse_qs(raw_data.decode('utf-8'))
    code = parsed_data.get('code', [None])[0]
    refresh_code = parsed_data.get('refresh_token', [None])[0]
    if code is not None:
        access_token = generate_access_token(code)
        refresh_token = refresh_access_token(code)
        response_data = { "token_type": "bearer", "access_token": access_token, "refresh_token": refresh_token, "expires_in": 86400 }
        return jsonify(response_data)
    if refresh_code is not None:
        access_token = generate_access_token_login(refresh_code)
        response_data = { "token_type": "bearer", "access_token": access_token, "refresh_token": refresh_code, "expires_in": 86400 }
        return jsonify(response_data)

@app.route('/get_device_details', methods=['GET'])
def get_device_detail():
    access_token = request.headers.get('Authorization')
    if not access_token or not access_token.startswith("Bearer "):
        return jsonify({"error": "No or invalid authorization token"}), 401

    access_token = access_token.replace("Bearer ", "")
    all_users_data = db.child("new_db").child("users").get().val()

    if not all_users_data:
        return jsonify({"error": "No user data found"}), 404

    for uid, user_data in all_users_data.items():
        bixby_data = user_data.get("bixby", {})
        if bixby_data.get("access_token") == access_token:
            device_id = []
            user_homes = user_data.get("homes", {})
            process_homes(user_homes, device_id)

            guest_data = db.child("new_db").child("users").child(uid).child("homes").child("access").get().val()
            if guest_data:
                for guest_home_id, access_info in guest_data.items():
                    owner_uid = access_info.get("owner_id")
                    if owner_uid:
                        owner_home_data = db.child("new_db").child("users").child(owner_uid).child("homes").child(guest_home_id).get().val()
                        if owner_home_data:
                            process_homes({guest_home_id: owner_home_data}, device_id)

            dev_product_id = [i["id"] + "_" + i["product_id"] for i in device_id]
            product_name = [i["name"] for i in device_id]
            return jsonify({"name": product_name, "device_id": dev_product_id})

    return jsonify({"error": "Unauthorized"}), 401

def process_homes(homes_data, device_id):
    try:
        for home_id, home_data in homes_data.items():
            rooms = home_data.get("rooms", {})
            for room_id, room_data in rooms.items():
                products = room_data.get("products", {})
                for product_id, product_data in products.items():
                    devices = product_data.get("devices", {})
                    for device_key, device_data in devices.items():
                        device_id.append({
                            "id": device_key,
                            "name": device_data.get("name"),
                            "product_id": product_id
                        })
    except Exception as e:
        print("Error:", e)

def generate_authorization_code(uid):
    characters = string.ascii_letters + string.digits
    authorization_code = ''.join(secrets.choice(characters) for _ in range(16))
    try:
        db.child("new_db").child("users").child(uid).child("bixby").update({"authorization_code": authorization_code})
    except:
        pass
    return authorization_code

def generate_access_token(code):
    users_data = db.child("new_db").child("users").get().val()
    if not users_data:
        return "None"

    try:
        for uid, user_data in users_data.items():
            bixby_data = user_data.get("bixby", {})
            if bixby_data.get("authorization_code") == code:
                access_token_prefix = "SamsungSmartThings|"
                characters = string.ascii_letters + string.digits
                random_part = ''.join(secrets.choice(characters) for _ in range(32))
                access_token = access_token_prefix + random_part
                db.child("new_db").child("users").child(uid).child("bixby").update({"access_token": access_token})
                return access_token

    except Exception as e:
        print(f"Error generating access token: {e}")
        return "None"

    return "None"

def generate_access_token_login(refresh_code):
    users_data = db.child("new_db").child("users").get().val()
    if not users_data:
        return "None"

    try:
        for uid, user_data in users_data.items():
            bixby_data = user_data.get("bixby", {})
            if bixby_data.get("refresh_token") == refresh_code:
                access_token_prefix = "SamsungSmartThings|"
                characters = string.ascii_letters + string.digits
                random_part = ''.join(secrets.choice(characters) for _ in range(32))
                access_token = access_token_prefix + random_part
                db.child("new_db").child("users").child(uid).child("bixby").update({"access_token": access_token})
                return access_token

    except Exception as e:
        print(f"Error generating access token with refresh token: {e}")
        return "None"

    return "None"

def refresh_access_token(code):
    users_data = db.child("new_db").child("users").get().val()
    if not users_data:
        return "None"

    try:
        for uid, user_data in users_data.items():
            bixby_data = user_data.get("bixby", {})
            if bixby_data.get("authorization_code") == code:
                access_token_prefix = "SamsungSmartThings|"
                characters = string.ascii_letters + string.digits
                random_part = ''.join(secrets.choice(characters) for _ in range(32))
                refresh_token = access_token_prefix + random_part
                db.child("new_db").child("users").child(uid).child("bixby").update({"refresh_token": refresh_token})
                return refresh_token
    except Exception as e:
        print(f"Error generating refresh token: {e}")
        return "None"

    return "None"

def refresh_token_to_refresh(existing_refresh_token):
    users_data = db.child("new_db").child("users").get().val()
    if not users_data:
        return "None"

    try:
        for uid, user_data in users_data.items():
            bixby_data = user_data.get("bixby", {})
            if bixby_data.get("refresh_token") == existing_refresh_token:
                access_token_prefix = "SamsungSmartThings|"
                characters = string.ascii_letters + string.digits
                new_refresh_token = ''.join(secrets.choice(characters) for _ in range(32))
                db.child("new_db").child("users").child(uid).child("bixby").update({"refresh_token": new_refresh_token})
                return new_refresh_token

    except Exception as e:
        print(f"Error refreshing the refresh token: {e}")
        return "None"

    return "None"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)