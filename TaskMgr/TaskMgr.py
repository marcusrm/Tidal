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
        'sap_work' : [], #worker results
        'sap_data' : "", #sapper results 
        'sap_rating' : [], #rates 
        'sap_reject' : [] #returns unsatisfactory taskids
    }

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

        workerId = self.get_argument("workerId",None)
        # assignmentId = self.get_argument("assignmentId",None)
        # hitId = self.get_argument("hitId",None)
        
        if( workerId is None ):
            self.write("some bad stuff happened on the way to hit page.")
            self.render("404.html")
            return
            
        self.render("hit.html",workerId=workerId)

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
    def get(self, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs
 
        # Handle WebSocket Origin naming convention differences
        # The difference between version 8 and 13 is that in 8 the
        # client sends a "Sec-Websocket-Origin" header and in 13 it's
        # simply "Origin".
        if "Origin" in self.request.headers:
            origin = self.request.headers.get("Origin")
        else:
            origin = self.request.headers.get("Sec-Websocket-Origin", None)

        # If there was an origin header, check to make sure it matches
        # according to check_origin. When the origin is None, we assume it
        # did not come from a browser and that it can be passed on.
        if origin is not None and not self.check_origin(origin):
            self.set_status(403)
            log_msg = "Cross origin websockets not allowed"
            self.finish(log_msg)
            gen_log.debug(log_msg)
            return 

        self.stream = self.request.connection.detach()
        self.stream.set_close_callback(self.on_connection_close)

        self.ws_connection = self.get_websocket_protocol()
        if self.ws_connection:
            self.ws_connection.accept_connection()
        else:
            if not self.stream.closed():
                self.stream.write(tornado.escape.utf8(
                    "HTTP/1.1 426 Upgrade Required\r\n"
                    "Sec-WebSocket-Version: 7, 8, 13\r\n\r\n"))
                self.stream.close()

    def check_origin(self, origin):
        parsed_origin = urlparse(origin)
        origin = parsed_origin.netloc
        origin = origin.lower()			
        host = self.request.headers.get("Host")
        print "Host : %s and origin = %s " %(host, origin)
        return True

    def on_message(self,evt):
        msg = tornado.escape.json_decode(evt)
        print "Socket msg is " #+ msg['mode']
        print msg

        # #response:
        blank = new_msg("chicken_selects","tiiiiid","select")
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
        
        print self
        
        workerId = self.get_argument("workerId",None)
        if(workerId is None or not wm.W.WIDexist(workerId)): 
            print "NO WORKER LOGGED IN"
            self.close()
        else:
            wm.W.set_socket(workerId,self)

        print "HI PEOPLE, I'M A WEBSOCKETTTTTTT"
        
        msg = new_msg("chicken_selects","tiiiiid","sap")
        msg['leaf_task'] = "floop the pig leaf"
        msg['branch_task'] = "floop the pig branch"
        msg['sap_task'] = ["floop the pig branch","DON'T GIVE EM THE STICK"]
        msg['sap_work'] = ["work1","work2, baby"]
        msg['sap_task_ids'] = ["ideeee1","id2"]
        self.write_message(tornado.escape.json_encode(msg))
        
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
