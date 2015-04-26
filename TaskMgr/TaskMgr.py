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


TaskTree = Tree()

def new_msg(WID, TID, mode, task="", profile={}):
    #header info

    msg = {
        'mode' : mode, #idle,ready,leaf,branch,sap,select
        'WID' : WID,
        'TID' : TID,
        'preference' : "", #leaf/branch/sap
        'time_end' : None,
        'time_start' : None,
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

    
#NOTE! when task can't find anything it should return
#a blank object with a TYPE of "idle"
def task_to_msg(task):
    msg = new_msg()
    msg['mode'] = task.type
    msg['WID'] = self.workerId
    msg['TID'] = task.TID
    msg['preference'] = self.preference
    msg['time_start'] = self.time_stamp
    msg['profile'] = self.profile
    if(task.type == "branch"):
        msg['branch_task'] = task.instructions
    if(task.type == "leaf"):
        msg['leaf_task'] = task.instructions
    if(task.type == "sap"):
        msg['sap_task'] = task.instructions
        msg['sap_task_ids'] = task.sap_task_ids
        msg['sap_work'] = task.sap_work
            
    return msg

class hitHandler(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        # global TaskId
        # print "\n****Get method " + str(TaskId);
        # hash_id = hashlib.sha512(str(TaskId)+salt).hexdigest();
        # print "Task ID: "+ hash_id
        # TaskId += 1;
        # TaskTree.add_node(hash_id);

        workerId = self.get_argument("workerId",None)
        # assignmentId = self.get_argument("assignmentId",None)
        # hitId = self.get_argument("hitId",None)
        
        if( workerId is None ):
            self.write("some bad stuff happened on the way to hit page.")
            self.render("404.html")
            return
            
        self.render("hit.html",workerId=workerId,
                    url_prefix=ts.URL_PREFIX,
                    port=ts.PORT,
                    local_testing=ts.LOCAL_TESTING)

    def post(self):
        # Accept task and 
        print "Task Submitted"
        TaskTree.add_node(hash_id);

# def doNextTask(id,ws):	
#     # NJ : 1. Check if you need more workers
#     # NJ : 2. Must pass next free task to the worker
#     worker_dict[id]['Task'] = '0' ; #get_task(); SB 
#     ws.write_message("WakeUp"); #placeholder msg - temp 
#     return True

# def send_msg_to_socket(msg):
#     socket = wm.W.get_socket(msg['WID'])
#     socket.write_message(msg)

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def send_msg(self,msg):
        self.write_message(tornado.escape.json_encode(msg))
    
    def idle_callback(self,msg):
        #remove worker from idle list #NJ
        print "idle callback" #???
        
    def ready_callback(self,msg): #NJ help 
        #assign pre-fetched task 
        #send msg back
        print "ready callback" #???

    def task_callback(self,msg):
        if(msg['mode'] != "select"):
            TaskTree.save_results(msg_to_task(msg))
        task = TaskTree.get_task("branch")
        self.send_msg(task_to_msg(task))
        print "task callback" 

    def select_callback(self,msg):
        wm.W.set_type(self.workerId,msg['preference'])
        self.preference = msg['preference']
        #jump to leaf/branch/sap to grab a new task:
        self.callback[self.preference](msg) 
        print "select callback"

        
    def __init__(self, application, request, **kwargs):
        super(WebSocketHandler, self).__init__(application, request, **kwargs)
        self.workerId = self.get_argument("workerId",None)
        self.callback = {"select" : self.select_callback,
                         "idle" : self.idle_callback,
                         "ready" : self.ready_callback,
                         "branch" : self.task_callback,
                         "leaf" : self.task_callback,
                         "sap" : self.task_callback,
                     }
        self.time_stamp = datetime.utcnow()
        self.preference = ""
        self.profile = None
        
    @tornado.web.asynchronous
    def get(self, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs
 
        if "Origin" in self.request.headers:
            origin = self.request.headers.get("Origin")
        else:
            origin = self.request.headers.get("Sec-Websocket-Origin", None)

        if origin is not None and not self.check_origin(origin):
            self.set_status(403)
            log_msg = "Cross origin websockets not allowed"
            self.finish(log_msg)
            gen_log.debug(log_msg)
            print "origin trouble"
            return 

        self.stream = self.request.connection.detach()
        self.stream.set_close_callback(self.on_connection_close)

        self.ws_connection = self.get_websocket_protocol()
        if self.ws_connection:
            self.ws_connection.accept_connection()
        else:
            if not self.stream.closed():
                print "stream trouble"
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
        
        #enforce correct timing & start new period. 
        msg['time_start'] = self.time_stamp
        msg['time_end'] = datetime.utcnow()
        self.time_stamp = datetime.utcnow()
        
        if(self.callback[msg['mode']] is not None):
            self.callback[msg['mode']](msg)
            

    def open(self): # args contains the argument of the forms
        if(self.workerId is None or not wm.W.WIDexist(self.workerId)): 
            print "WORKER NOT LOGGED IN"
            self.close()
            return
        else:
            wm.W.set_socket(self.workerId,self)
            
        selectmsg = new_msg(self.workerId,"","select")
        self.send_msg(selectmsg)
        
        # self.stream.set_nodelay(True) #what's this?

    def on_close(self):
        print "Closing socket for" + self.workerId
        wm.W.logout(self.workerId)
