import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

#get hardware config
with open('/home/pi/access_config.json') as f:
  access_config = json.load(f)

cred = credentials.Certificate(str(access_config["firebase"])) #contains path to keyFile
firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.collection(u'user').document(u'avi')
doc_ref.set({
	u"email": u"testuser@oasisregenerative.com",
	u"fullName" : u"Test Account",
	u"id" : 7
})

