# app/fga.py

from openfga_sdk.client import ClientConfiguration
from openfga_sdk.sync import OpenFgaClient
from flask import current_app

# We default fga_client to None until it is initialized
fga_client = None

def initialize_fga_client():
    # This function is called to initialize our FGA Client instance if it is not already available
    print("Initializing OpenFGA Client SDK")
    configuration = ClientConfiguration(
        api_url = current_app.config['FGA_API_URL'], 
        store_id = current_app.config['FGA_STORE_ID'], 
        authorization_model_id = current_app.config['FGA_MODEL_ID'], 
    )

    global fga_client
    fga_client = OpenFgaClient(configuration)
    fga_client.read_authorization_models()
    print("FGA Client initialized.")
    