#!/usr/bin/python2
#handle sockets 

import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.template
import os.path
import uuid
from urlparse import urlparse  # py3
import hashlib
# Task Tree Imports
from tree import Tree
import copy
import myconst


import sys
sys.path.append('../')
import tidal_settings as ts
import tidal_auth as ta
import tidal_amt as t_amt
import WorkMgr as wm
import tidal_msg as tms
from datetime import datetime

#debug
from pdb import set_trace as brk


TaskTree    = Tree()

#NOTE! when task can't find anything it should return
#a blank object with a TYPE of "idle"
def task_to_msg(task):
   
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

def msg_wsh(msg,wsh):
    msg['WID'] = wsh.workerId
    msg['preference'] = wsh.preference
    #msg['time_start'] = wsh.time_stamp
    msg['profile'] = wsh.profile
    return msg

class hitHandler(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        tid = uuid.uuid4().hex
        TaskTree.add_node(tid);
        workerId = self.get_argument("workerId",None)
        assignmentId = self.get_argument("assignmentId",None)
        hitId = self.get_argument("hitId",None)
        turkSubmitTo = self.get_argument("turkSubmitTo",None)
        
        if( workerId is None or hitId is None or assignmentId is
            None or turkSubmitTo is None ):
            self.write("some bad stuff happened on the way to the hit page.")
            self.render("404.html")
            return
            
        self.render("hit.html",workerId=workerId,
                    assignmentId=assignmentId,
                    hitId=hitId,
                    turkSubmitTo=turkSubmitTo+"/mturk/externalSubmit",
                    url_prefix=ts.URL_PREFIX,
                    port=ts.PORT,
                    local_testing=ts.LOCAL_TESTING)

    def post(self):
        #should probably do some cleanup here...
        #like closing the users websocket, etc.
        print "Task Submitted"


def send_task(msg):
    #print msg
    socket = wm.W.get_socket(msg['WID'])
    socket.send_msg(msg_wsh(msg,socket))

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def fill_msg_wsh(self,tid):
        msg = tms.new_msg()
        msg = copy.deepcopy(TaskTree.getmsgcp(tid));
        msg['WID']          = self.workerId
        msg['preference']   = self.preference
        #msg['time_start']   = self.time_stamp
        msg['profile']      = self.profile
        msg['mode']         = 'branch'
        print "Sending to ws of worker "+msg['WID']
        return msg

    def shake_tree(self):
        try:
            elem = TaskTree.get_q_len()
            print 'Task Q length is '+str(elem)
        except:
            print '0 elements in queue'

        try:                                                 # get a task to assign
            tq = TaskTree.get_q_elem()
            print 'queue id is ' + str(tq)
        except:
            print "Exception in shake_tree : No tasks available"
            return 

        wid = wm.W.assign('branch',tq[1])               # find a free worker 
        if(wid):
            ws = wm.W.get_socket(wid)
            msg = ws.fill_msg_wsh(tq[1])
            print 'Sending a msg to show task ' + str(tq[1])+'to worker ' + wid
            send_task(msg)
            return
        else:   
            TaskTree.add_to_q(tq[0],tq[1])
            return 0

    def send_msg(self,msg):
        self.write_message(tornado.escape.json_encode(msg))

    def logout_callback(self,msg):
        self.close()
        
    def idle_callback(self,msg):
        #waiting on API
        #min = (msg['time_end']-msg['time_start']).total_seconds() / float(60)
        #print "adding idle min:", min
        #wm.W.addIdleTime(self.workerId,min)
        print "idle callback"
        
    def ready_callback(self,msg):
        #tree.release_ready_TID(msg.TID);
        #assign pre-fetched task 
        #send msg back
        print "ready callback" #???

    def task_callback(self,msg):
        #waiting on API
        #min = (msg['time_end']-msg['time_start']).total_seconds() / float(60)
        #print "adding active min:", min
        #wm.W.addActiveTime(self.workerId,min)
        TaskTree.save_results(msg)                       # save results of the task
        TaskTree.wait_for_approval(msg['TID'],msg['WID'])# send msg over socket to wait for approval
        TaskTree.ask_approval(msg['TID'])                # send msg to parent to approve 
        wm.W.complete(self.workerId,msg['TID'],0.05)     # Payment

        self.shake_tree();                               # Look to match more work and tasks
        #self.send_msg(tm.new_msg(self.workerId,"","idle"),self))#fill in params more completely

        print "task callback" 

    def select_callback(self,msg):
        wm.W.set_type(self.workerId,msg['preference'])
        self.preference = msg['preference']
        self.send_msg(tms.new_msg(mode="idle",WID=self.workerId,TID=""))#fill in params more completely
        print "select callback shake starts"
        self.shake_tree();                              # Look to match more work and tasks
        print "select callback shake returns"
    
    def __init__(self, application, request, **kwargs):
        super(WebSocketHandler, self).__init__(application, request, **kwargs)
        self.workerId = self.get_argument("workerId",None)
        self.hitId = self.get_argument("hitId",None)
        self.callback = {"select" : self.select_callback,
                         "idle" : self.idle_callback,
                         "ready" : self.ready_callback,
                         "branch" : self.task_callback,
                         "leaf" : self.task_callback,
                         "sap" : self.task_callback,
                         "super" : self.task_callback,
                         "logout": self.logout_callback,
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
        print "Shruthi onmsg"

        msg = tornado.escape.json_decode(evt)
        #print msg['branch_data']
        #enforce correct timing & start new period. 
        msg['time_start'] = self.time_stamp
        msg['time_end'] = datetime.utcnow()
        self.time_stamp = datetime.utcnow()
        
        # S1. Store task's results 
        if(self.callback[msg['mode']] is not None):
            self.callback[msg['mode']](msg)
            

    def open(self): # args contains the argument of the forms
        if(self.workerId is None or not wm.W.WIDexist(self.workerId)): 
            print "WORKER NOT LOGGED IN"
            self.close()
            return
        else:
            wm.W.set_socket(self.workerId,self)
        selectmsg = tms.new_msg(mode="select",WID=self.workerId,TID="")
        self.send_msg(selectmsg)
        
    def on_close(self):
        print "Closing socket for" + self.workerId
        #WAITING ON API
        # TID = wm.W.getTID(self.workerId)
        # print "aborting task: ",TID
        # tree.abort_task(TID)
        
        #self.send_msg(tmsg.new_msg(mode="logout",WID=self.workerId,TID=""));
        
        #BUSY WAIT FOR AMT TO RESPOND.
        while(t_amt.get_hit(self.hitId).num_submitted != 0):
            continue;

        t_amt.delete_amt_hit(self.hitId)
        
        wm.W.logout(self.workerId)

