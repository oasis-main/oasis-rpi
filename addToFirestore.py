import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("/home/pi/oasis-1757f-firebase-adminsdk-i71b5-e9142f842a.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc_ref = db.collection(u'user').document(u'avi')
doc_ref.set({
	u"email": u"ahayes@secondkeys.com",
	u"fullName" : u"Amber",
	u"id" : 1
})

