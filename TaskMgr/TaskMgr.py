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
import WorkMgr as wm
import json
from datetime import datetime

TaskTree = Tree()
TaskId = 0
salt = 'clutter'
workers = [ ]
worker_dict = {}

def new_msg(WID, TID, mode, task="", profile={}):
    #header info
    msg = {}
    msg.mode = mode #idle,ready,leaf,branch,sap,select
    msg.WID = WID
    msg.TID = TID
    msg.preference = "" #leaf/branch/sap
    msg.time_end = None
    msg.time_start = str(datetime.utcnow())
    msg.profile = profile

    #branch info
    msg.branch.task = "" #instructions
    msg.branch.data = [] #worker results for each new branch
    msg.branch.data_type = [] #is each result a leaf or a branch

    #leaf info
    msg.leaf.task = "" #instructions 
    msg.leaf.data = "" #worker results

    #sap info
    msg.sap.task = [] #instructions (solutions from each TID)
    msg.sap.task_ids = [] #matching TIDs for the instructions
    msg.sap.data = "" #worker results 
    msg.sap.rating = [] #rates 
    msg.sap.rejection = [] #returns unsatisfactory taskids

    if(mode == "branch"):
        msg.branch.task = task #instructions
    if(mode == "leaf"):
        msg.leaf.task = task #instructions
    if(mode == "sap"):
        msg.sap.task = task #instructions

    return msg


class hitHandler(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        global TaskId
        print "\n****Get method " + str(TaskId);
        hash_id = hashlib.sha512(str(TaskId)+salt).hexdigest();
        print "Task ID: "+ hash_id
        TaskId += 1;
        TaskTree.add_node(hash_id);
        
        msg=new_msg(workerId,"","idle")
        self.render("hit.html", msg=msg)

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

    def on_message(self,jmsg):
        msg = json.loads(jmsg)
        print "Socket msg is " + msg.type;
            
        # NJ: msg must include all task info;Add it to DB 
        if(msg.type == "AddTasks"):
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
        if(msg.type == ""):
            stop=1
                        

    def open(self,jmsg): # args contains the argument of the forms

        msg = json.loads(jmsg)
        wm.W.set_socket(msg.WID,self)
        
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
        wm.W.logout(self.id)

# def main():
# 	application = tornado.web.Application(
# 		[
# 		    (r"/", MainHandler),
# 		    (r"/websocket", WebSocketHandler),
# 			],
# 		static_path=os.path.join( os.path.dirname(__file__), "static"),
# 		template_path=os.path.join( os.path.dirname(__file__), "templates"),
# 		debug=True
# 		)
# 	application.listen(8888)
# 	tornado.ioloop.IOLoop.instance().start()

# if __name__ == "__main__":
# 	main()
