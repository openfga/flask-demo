# app/routes.py

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Resource, db
from .fga import get_fga_client
from openfga_sdk.client.models import ClientTuple, ClientWriteRequest, ClientCheckRequest

main = Blueprint('main', __name__)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('main.register'))

        user = User(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

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
    fga_client = get_fga_client()
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
    fga_client = get_fga_client()
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
