import sqlite3					#Calls SQLite for Database handling
from contextlib import closing 	#Initializes database for application
import os,sys
import socket

DATABASE=os.path.join(os.path.dirname(sys.argv[0]),'WorkerDB.db')
SCHEMA=os.path.join(os.path.dirname(sys.argv[0]),'WorkerSchema.sql')

# Connects the application to the database
def connect_db():
	return sqlite3.connect(DATABASE)
	
# Initializes the database
def init_db():
    with closing(connect_db()) as db:
        with open(SCHEMA, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
	
# Called before a request is made
@app.before_request
def before_request():
    g.db = connect_db()
		
		
# Called only if an exception is raised during a after_request()
@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close() 


# Show entries in the server window		
def show_entry():
	cur = g.db.execute('select Id, Name, StudName from entries order by id desc')
	lastentry=cur.fetchone()
	print("\nDatabase Entry #"+str(lastentry[0])+':'+lastentry[1]+" commented on "+lastentry[2]+" was succesfully posted")
	return lastentry

	
# Load the data from the forms into the database
@app.route('/', methods=['POST'])
def add_entry():
	ClientData=json.loads(request.form['ClientTag'])
	ClientData["RecvTime"]=datetime.utcnow();
	
	# Unpacking info from the ClientData dict to form keys and values for injecting into sqlite3
	columns = ', '.join(ClientData.keys())											# Extract keys from dict
	placeholders = ', '.join('?' * len(ClientData))									# Create list of '?' equal to same length as dict
	sql = 'INSERT INTO entries ({}) VALUES ({})'.format(columns, placeholders)		# Combine information
	g.db.execute(sql,list(ClientData.values()))										# Execute command and create new entry
	g.db.commit()																	# Commit it to the database
	g.db.commit() 																	# just for precaution
	show_entry()
	return redirect('/')
	
# Check to see if database exists
if os.path.exists(DATABASE)==False:
	print("Database Doesn't Exist, creating it...")
	init_db();
	print("Database Created")
else:
	print("Database linked")
	