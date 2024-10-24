# app/fga.py

from openfga_sdk.client import ClientConfiguration
from openfga_sdk.sync import OpenFgaClient
from flask import current_app

def get_fga_client():
    config = ClientConfiguration(
        api_url=current_app.config['FGA_API_URL'],
        store_id=current_app.config['FGA_STORE_ID'],
        authorization_model_id=current_app.config['FGA_MODEL_ID'],
    )
    client = OpenFgaClient(config)
    return client
