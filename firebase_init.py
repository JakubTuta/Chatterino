import firebase_admin
from firebase_admin import credentials, db, firestore

cred = credentials.Certificate("./firebase_config.json")
firebase_admin.initialize_app(cred)

db_ref = db.reference(
    url="https://chatterino-3d2e7-default-rtdb.europe-west1.firebasedatabase.app"
)

gc = firestore.client()
