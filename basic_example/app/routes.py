# app/routes.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Resource, db
from .fga import fga_client, initialize_fga_client
from urllib.parse import quote_plus, urlencode
from openfga_sdk.client.models import ClientTuple, ClientWriteRequest, ClientCheckRequest
from app import oauth
import uuid
from functools import wraps

main = Blueprint('main', __name__)

current_user = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This decorated function can be applied to route handers and will ensure that a valid user session is active.
        # If the requestor is not logged in it will redirect their browser to the home page
        if 'user' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def registerUser(user_info):
    # This function is used when a user logs into the app for the first time.
    # It creates an entry in the database for the user and creates a default folder for them
    email = user_info['email']
    name = user_info['name']
    
    new_uuid = uuid.uuid4()
    print(f"Registering New User {new_uuid} in Database")

    user = User(email=email, name=name, uuid=new_uuid)
    db.session.add(user)
    db.session.commit()
    print("User Registered in database")

    return True

def loadSession(email):
    # This function is used after a user has authenticated to set the needed session variables so they can
    # be accessed by other route handlers in the application
    print(f"Loading User Info from database for {email}")
    user = User.query.filter_by(email=email).first()

    if user is None:
        return False
    
    session["user_id"] = user.id
    session["uuid"] = user.uuid
    session["name"] = user.name
    curent_user = user

    return True

@main.route("/login")
def login():
    # Login function redirects to the Auth0 login page for our app
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True)
    )

@main.route("/callback", methods=["GET", "POST"])
def callback():
    # The callback function that Auth0 will redirect users to after authentication
    try:
        token = oauth.auth0.authorize_access_token()
        print(f"TOKEN: {token}\n\n\n")
        session["user"] = token

        user_info = token['userinfo']
        

        user = User.query.filter_by(email=user_info['email']).first()
        if user is None:
            registerUser(user_info)
        else:
            print("User is already registered.")

        loadSession(user_info['email'])

    except Exception as e:
        print(f"Error: {e}\n\n")
        return redirect(url_for("main.home"))
    return redirect(url_for("main.home"))
    

@main.route("/logout")
def logout():
    # Log a user out of the app, clear the session and redirect them to the Auth0 logout url for our app
    session.clear()
    return redirect(
        "https://" + current_app.config["AUTH0_DOMAIN"]
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main.home", _external=True),
                "client_id": current_app.config["AUTH0_CLIENT_ID"],
            },
            quote_via=quote_plus,
        )
    )

@main.route('/')
@login_required
def index():
    resources = Resource.query.all()
    return render_template('index.html', resources=resources)

@main.route('/create_resource', methods=['POST'])
@login_required
def create_resource():
    resource_name = request.form.get('name')

    resource = Resource(name=resource_name, owner=current_user)
    db.session.add(resource)
    db.session.commit()

    # Create a tuple in OpenFGA
    if fga_client is None:
        initialize_fga_client()
    write_request = ClientWriteRequest(
        writes=[
            ClientTuple(
                user=f"user:{current_user.uuid}",
                relation="owner",
                object=f"resource:{resource.uuid}",
            ),
        ],
    )
    fga_client.write(write_request)

    return redirect(url_for('main.resource', resource_uuid=resource.uuid))

@main.route('/resource/<resource_uuid>')
@login_required
def resource(resource_uuid):
    resource = Resource.query.filter_by(uuid=resource_uuid).first()
    if not resource:
        flash('Resource not found.')
        return redirect(url_for('main.index'))

    # Check permission using OpenFGA
    if fga_client is None:
        initialize_fga_client()
    check_request = ClientCheckRequest(
        user=f"user:{current_user.uuid}",
        relation="viewer",
        object=f"resource:{resource.uuid}",
    )
    response = fga_client.check(check_request)

    if not response.allowed:
        flash('You do not have permission to view this resource.')
        return redirect(url_for('main.index'))

    return render_template('resource.html', resource=resource)