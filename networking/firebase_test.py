import os
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import concurrent_state_new as cs

cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ['GOOGLE_DATABASE_URL']
})

def patch_firebase(json):
    ref = db.reference("device_state")
    ref.set(str(json))

if __name__ == "main":
    cs.load_state()
    json = cs.device_state
    patch_firebase(str(json))