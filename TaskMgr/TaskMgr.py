#!/usr/bin/python2
#handle sockets 

import tornado.web
import tornado.websocket
import tornado.ioloop
import os.path
from urlparse import urlparse  # py3
import hashlib
# Task Tree Imports
from tree import Tree
import myconst

import sys
sys.path.append('../')
import tidal_settings as ts
import tidal_auth as ta

TaskTree = Tree()
TaskId = 0
salt = 'clutter'
workers = [ ]
worker_dict = {}
class hitHandler(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
    	global TaskId
    	print "\n****Get method " + str(TaskId);
    	hash_id = hashlib.sha512(str(TaskId)+salt).hexdigest();
    	print "Task ID: "+ hash_id
    	TaskId += 1;
    	TaskTree.add_node(hash_id);
        self.render("taskpage.html", ptaskid=hash_id)

    def post(self):
    	# Accept task and 
    	print "Task Submitted"
    	TaskTree.add_node(hash_id);

def doNextTask(id,ws):	
	# NJ : 1. Check if you need more workers
	# NJ : 2. Must pass next free task to the worker
	worker_dict[id]['Task'] = '0' ; #get_task(); SB 
	ws.write_message("WakeUp"); #placeholder msg - temp 
	return True

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	count = 0;
	t2wcount = 1;
	@tornado.web.asynchronous
	def check_origin(self, origin):
		parsed_origin = urlparse(origin)
		origin = parsed_origin.netloc
		origin = origin.lower()			
		host = self.request.headers.get("Host")
		print "Host : %s and origin = %s " %(host, origin)
		return True

	def on_message(self,msg):
		print "Socket msg is " + msg;

		# NJ: msg must include all task info;Add it to DB 
		if(msg == "AddTasks"):
			#NJ: Pick a free worker from the list
			#workerId = get_worker();
			workerId = str(WebSocketHandler.t2wcount);
			print" Searching for Worker with ID "+workerId
			if workerId in worker_dict:
				workerWS = worker_dict[workerId]['Ws'];
				print "Worker WS selected for next task"
				if(doNextTask(workerId,workerWS)):
					worker_dict[workerId]['Status'] = 'busy'
					print "Next task assigned to" + workerId
					WebSocketHandler.t2wcount+=1;
				else:
					print "Failed to assign Task to worker"
			else:
				self.write_message("Msg="+msg)


	def open(self,*args): # args contains the argument of the forms
		self.id = WebSocketHandler.count # RJ: You have to replace thsi with worker ID here.
		id =  str(self.id)
		WebSocketHandler.count += 1
		print "Opened socket with id "+ str(self.id)
		self.write_message("Opened task")
		self.stream.set_nodelay(True)
		# Store current context information using the socket object
		workers.append(self)
		worker_dict[id] = {}
		worker_dict[id]['Ws']= self 
		worker_dict[id]['Task']= ''
		worker_dict[id]['Status'] = 'idle'
		if (WebSocketHandler.count == 1):
			self.write_message("GenPage")
		return True


	def on_close(self):
			print "Closing socket " + str(self.id)

def main():
	application = tornado.web.Application(
		[
		    (r"/", MainHandler),
		    (r"/websocket", WebSocketHandler),
			],
		static_path=os.path.join( os.path.dirname(__file__), "static"),
		template_path=os.path.join( os.path.dirname(__file__), "templates"),
		debug=True
		)
	application.listen(8888)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
