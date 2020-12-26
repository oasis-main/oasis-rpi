#https://firebase.google.com/docs/reference/rest/auth
#https://github.com/thisbejim/Pyrebase
#https://firebase.google.com/docs/auth/admin/create-custom-tokens

import requests
import json
import pyrebase

def getNewRefreshToken(web_api_key,email,password):
	sign_in_url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=" + web_api_key
	sign_in_payload = json.dumps({"email": email, "password": password, "returnSecureToken": "true"})
	r = requests.post(sign_in_url, sign_in_payload)
	data = json.loads(r.content)
	return data['refreshToken']


web_api_key = 'AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc'
email = "b@b.com"
password = '123456'
getNewRefreshToken(web_api_key,email,password)



