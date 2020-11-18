
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

def detect_feild_event(user, db, feild):
	my_stream = db.child(user['userId']+'/'+feild).stream(stream_handler, user['idToken'], stream_id=feild)


#https://stackoverflow.com/questions/2046603/is-it-possible-to-run-function-in-a-subprocess-without-threading-or-writing-a-se
#https://stackoverflow.com/questions/200469/what-is-the-difference-between-a-process-and-a-thread#:~:text=A%20process%20is%20an%20execution,sometimes%20called%20a%20lightweight%20process.
#run multiprocesser to handle database listener
#could use threads in future? would it be better?
def detect_multiple_feild_events(user, db, feilds):
	for feild in feilds:
		p = Process(target=detect_feild_event, args=(user, db, feild))
		p.start()

#make change to config file
def act_on_event(feild, new_data):
	#get data and feild info
	#open data config file
	#edit appropriate spot
	with open('/Users/avielstein/Desktop/config.json', 'r+') as r:
		data = json.load(r)
		data[feild] = new_data
		r.seek(0) # <--- should reset file position to the begi$
		json.dump(data, r)
	r.close()


if __name__ == '__main__':
	RefreshToken = 'AG8BCnc3HIku8dmoofrvTZ6Ib3NBLgc6r1GlinahFadxnTvk6DqpoDUdb3w2FklbfNMozHDJHideuDTksEI8GgbwH9ixQtPkZDZ0xwUyLS9EBJuIv0Fn4TaBPO1aSciWIqhfJrp_YFtLkUfMimXkDny7UtA3NnYtHaWmorZsiFc-hmGj0XzXkjOQmUXOg1lc21qoxVbOHgUq'
	user, db = initialize_user(RefreshToken)
	#print(get_user_data(user, db))
	#detect_feild_event(user, db, 'set_temp')
	feilds = ['set_temp','set_humid']
	detect_multiple_feild_events(user, db, feilds)





