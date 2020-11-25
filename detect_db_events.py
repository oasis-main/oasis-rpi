
#https://stackoverflow.com/questions/58354509/modulenotfounderror-no-module-named-python-jwt-raspberry-pi
#https://github.com/thisbejim/Pyrebase
#https://stackoverflow.com/questions/45154853/how-to-detect-changes-in-firebase-child-with-python


#this may be helpful if i cant figure something else out for updating values
#https://pypi.org/project/FirebaseData/


#This may be the thing to do
#https://github.com/thisbejim/Pyrebase/issues/341

#OTHER
#________________
#https://stackoverflow.com/questions/62301320/pyrebase-and-firebase-database-rules-how-to-deal-with-it-with-python
#https://www.reddit.com/r/Firebase/comments/idhdji/how_can_i_store_data_under_a_user_id_with_pyrebase/g2bcvhz/
#https://medium.com/@parasmani300/pyrebase-firebase-in-flask-d249a065e0df
#https://stackoverflow.com/questions/54838847/pyrebase-stream-retrived-data-access


import pyrebase
from multiprocessing import Process, Queue
import json
import os


def initialize_user(RefreshToken):

	#app configuration information
	config = {
	  "apiKey": "AIzaSyD-szNCnHbvC176y5K6haapY1J7or8XtKc",
	  "authDomain": "oasis-1757f.firebaseapp.com",
	  "databaseURL": "https://oasis-1757f.firebaseio.com/",
	  "storageBucket": "gs://oasis-1757f.appspot.com"
	}

	firebase = pyrebase.initialize_app(config)

	# Get a reference to the auth service
	auth = firebase.auth()

	# Get a reference to the database service
	db = firebase.database()

	#WILL NEED TO GET THIS FROM USER
	user = auth.refresh(RefreshToken)

	return user, db

#get all user data
def get_user_data(user, db):
	return  db.child(user['userId']).get(user['idToken']).val()

def stream_handler(m):

	#ok some kind of update
	#might be from start up or might be user changed it
	if m['event']=='put':
		act_on_event(m['stream_id'],m['data'])

	#something else
	else:
		pass
		#if this happens... theres a problem...
		#should be handled for
		print('something wierd...')

def detect_field_event(user, db, field):
	my_stream = db.child(user['userId']+'/'+field).stream(stream_handler, user['idToken'], stream_id=field)


#https://stackoverflow.com/questions/2046603/is-it-possible-to-run-function-in-a-subprocess-without-threading-or-writing-a-se
#https://stackoverflow.com/questions/200469/what-is-the-difference-between-a-process-and-a-thread#:~:text=A%20process%20is%20an%20execution,sometimes%20called%20a%20lightweight%20process.
#run multiprocesser to handle database listener
#could use threads in future? would it be better?
def detect_multiple_field_events(user, db, fields):
	for field in fields:
		p = Process(target=detect_field_event, args=(user, db, field))
		p.start()

#make change to config file
def act_on_event(field, new_data):
	#get data and field info

	#checks if file exists and makes a blank one if not
	#the path has to be set for box
	device_state_fields = ["connected", "running", "LEDstatus", "AccessPoint", "LEDtimeon", "LEDtimeoff"]

        grow_params_fields = ["targetT", "targetH", "targetL", "LtimeOn", "LtimeOff", "lightInterval", "cameraInterval", "waterMode", "waterDuration", "waterInterval"]

        if str(field) in device_state_fields:
            path = '/home/pi/device_state.json'
        if str(field) in grow_params_fields:
            path = '/home/pi/grow_params.json'

	if os.path.exists(path) == False:
		f = open(path, "w")
		f.write("{}")
		f.close()

	#open data config file
	#edit appropriate spot
	with open(path, 'r+') as r:
		data = json.load(r)
		data[str(field)] = str(new_data)
		r.seek(0) # <--- should reset file position to the beginning
		json.dump(data, r)
	r.close()


if __name__ == '__main__':
	RefreshToken = 'AG8BCnc3HIku8dmoofrvTZ6Ib3NBLgc6r1GlinahFadxnTvk6DqpoDUdb3w2FklbfNMozHDJHideuDTksEI8GgbwH9ixQtPkZDZ0xwUyLS9EBJuIv0Fn4TaBPO1aSciWIqhfJrp_YFtLkUfMimXkDny7UtA3NnYtHaWmorZsiFc-hmGj0XzXkjOQmUXOg1lc21qoxVbOHgUq'
	user, db = initialize_user(RefreshToken)
	#print(get_user_data(user, db))
	#detect_field_event(user, db, 'set_temp')
	fields = ['set_temp','set_humid']
	detect_multiple_field_events(user, db, fields)





