#!/usr/bin/python2
#handle sockets 

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.template
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
from datetime import datetime
import json


TaskTree = Tree()
TaskId = 0
salt = 'clutter'
workers = [ ]
worker_dict = {}

def new_msg(WID, TID, mode, task="", profile={}):
    #header info

    msg = {
        'mode' : mode, #idle,ready,leaf,branch,sap,select
        'WID' : WID,
        'TID' : TID,
        'preference' : "", #leaf/branch/sap
        'time_end' : None,
        'time_start' : str(datetime.utcnow()),
        'profile' : profile,

    #branch info
        'branch_task' : "", #instructions
        'branch_data' : [], #worker results for each new branch
        'branch_data_type' : [], #is each result a leaf or a branch

    #leaf info
        'leaf_task' : "", #instructions 
        'leaf_data' : "", #worker results

    #sap info
        'sap_task' : [], #instructions (solutions from each TID)
        'sap_task_ids' : [], #matching TIDs for the instructions
        'sap_data' : "", #worker results 
        'sap_rating' : [], #rates 
        'sap_rejection' : [] #returns unsatisfactory taskids
    }
    # if(mode == 'branch'):
    #     msg.branch.task = task #instructions
    # if(mode == 'leaf'):
    #     msg.leaf.task = task #instructions
    # if(mode == 'sap'):
    #     msg.sap.task = task #instructions

    return msg

class hitHandler(ta.BaseHandler):
    #@tornado.web.authenticated
    def get(self):
        global TaskId
        print "\n****Get method " + str(TaskId);
        hash_id = hashlib.sha512(str(TaskId)+salt).hexdigest();
        print "Task ID: "+ hash_id
        TaskId += 1;
        TaskTree.add_node(hash_id);

        workerId = self.get_argument("workerId",None)
        # assignmentId = self.get_argument("assignmentId",None)
        # hitId = self.get_argument("hitId",None)
        
        if( workerId is None ):#or hitId is None or assignmentId is None ):
            self.write("some bad stuff happened on the way to hit page.")
            self.render("404.html")
            return
            
        msg=new_msg(WID=workerId,TID="",mode="select")
        #msg=escapejs( json.dumps(msg, separators=(',',':')) )
        #msg=json.dumps(json.dumps(msg))
        self.render("hit.html",workerId=workerId)
       # self.render("hit.html", msg=tornado.escape.json_encode(msg) )

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

def send_msg(msg):
    socket = wm.W.get_socket(msg['WID'])
    socket.write_message(msg)

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

    def on_message(self,evt):
        msg = json.loads(evt)
        print "Socket msg is " + msg['mode']
        blank = new_msg("widdddd","tiiiiid","idle")
        self.write_message(tornado.escape.json_encode(blank))
            
        # NJ: msg must include all task info;Add it to DB 
        if(msg['mode'] == "AddTasks"):
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

                        

    def open(self): # args contains the argument of the forms
        
        workerId = self.get_argument("workerId",None)
        if(workerId is None): #or if worker is not logged in
            print "NO WORKER LOGGED IN"
            self.close()
        else:
            wm.W.set_socket(workerId,self)

        print "HI PEOPLE, I'M A WEBSOCKETTTTTTT"
        
        # self.id = WebSocketHandler.count # RJ: You have to replace thsi with worker ID here.
        # id =  str(self.id)
        # WebSocketHandler.count += 1
        # print "Opened socket with id "+ str(self.id)
        # self.write_message("Opened task")
        # self.stream.set_nodelay(True)
        # # Store current context information using the socket object
        # workers.append(self)
        # worker_dict[id] = {}
        # worker_dict[id]['Ws']= self 
        # worker_dict[id]['Task']= ''
        # worker_dict[id]['Status'] = 'idle'
        # if (WebSocketHandler.count == 1):
        #     self.write_message("GenPage")
        #     return True
        

    def on_close(self):
        pass
        #print "Closing socket " + str(self.id)
        #wm.W.logout(self.id)

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
