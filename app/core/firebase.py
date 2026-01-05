import json
import os
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    if firebase_admin._apps:
        return

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

    if not service_account_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT env var not set")

    cred = credentials.Certificate(json.loads(service_account_json))
    firebase_admin.initialize_app(cred)
