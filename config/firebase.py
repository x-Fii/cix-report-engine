import os
import firebase_admin
from firebase_admin import credentials, auth

CREDENTIAL_PATH = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(CREDENTIAL_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': 'service-form-496306',
        })

init_firebase()
