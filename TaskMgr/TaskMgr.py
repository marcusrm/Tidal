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
from tree import TaskTree
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


# #NOTE! when task can't find anything it should return
# #a blank object with a TYPE of "idle"
# def task_to_msg(task):
   
#     msg['mode'] = task.type
#     msg['WID'] = self.workerId
#     msg['TID'] = task.TID
#     msg['preference'] = self.preference
#     msg['time_start'] = self.time_stamp
#     msg['profile'] = self.profile
#     if(task.type == "branch"):
#         msg['branch_task'] = task.instructions
#     if(task.type == "leaf"):
#         msg['leaf_task'] = task.instructions
#     if(task.type == "sap"):
#         msg['sap_task'] = task.instructions
#         msg['sap_task_ids'] = task.sap_task_ids
#         msg['sap_work'] = task.sap_work
            
#     return msg

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
        TaskTree.add_node(tid)
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
    print msg['WID'] + '=Socket to write'
    socket = wm.W.get_socket(msg['WID'])
    socket.send_msg(msg_wsh(msg,socket))

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def fill_msg_wsh(self,tid,mode='ready'):
        msg = tms.new_msg()
        msg = copy.deepcopy(TaskTree.getmsgcp(tid))
        msg['WID']          = self.workerId
        msg['preference']   = self.preference
        #msg['time_start']   = self.time_stamp
        msg['profile']      = self.profile
        msg['mode']         = mode
        print "Sending to ws of worker "+msg['WID']
        return msg

    def shake_tree(self,mode=None):
        elem = TaskTree.get_q_len()
        for i in range(1,elem+1):                       # get a task to assign
            tq = TaskTree.get_q_elem()                  # get a task to assign
            print 'shake_tree: NewQlen=' + str(elem) + 'Task got is ' + str(tq)
            wid = wm.W.assign('branch',tq[1])               # Get a free worker to do the task picked above
            if(wid):
                ws = wm.W.get_socket(wid)
               # ws.write_message('Shruthi-try')
                msg = ws.fill_msg_wsh(tq[1],mode='branch')
                print 'Sending a msg to show task ' + str(tq[1])+'to worker ' + wid
                #print 'Socket of wid is ' + str(ws.workerId)
        
                #important step for sending ready msgs:
                #hide the mode of the message in preference to know
                #what content to preview to worker. 
                msg['preference']=msg['mode']
                msg['mode']="ready"            
                
                send_task(msg)
                #todo:msg = ws.fill_msg_wsh(tq[1])
            else:
                print 'Warning - no workers'   
                TaskTree.add_to_q(tq[0],tq[1])              # Put the task back in the queue
                break

    def shake_tree_sap(self,mode=None):
        elem = TaskTree.get_sq_len()
        for i in range(1,elem+1):                       # get a task to assign
            sq = TaskTree.get_sq_elem()                  # get a task to assign
            print 'shake_tree: NewQlen=' + str(elem) + 'Task got is ' + str(sq)
            wid = wm.W.assign('branch',sq[1])               # Get a free worker to do the task picked above
            if(wid):
                ws = wm.W.get_socket(wid)
               # ws.write_message('Shruthi-try')
                msg = ws.fill_msg_wsh(sq[1],mode='branch')
                print 'Sending a msg to show task ' + str(sq[1])+'to worker ' + wid
                #print 'Socket of wid is ' + str(ws.workerId)
        
                #important step for sending ready msgs:
                #hide the mode of the message in preference to know
                #what content to preview to worker. 
                msg['preference']=msg['mode']
                msg['mode']="ready"            
                
                send_task(msg)
                #todo:msg = ws.fill_msg_wsh(sq[1])
            else:
                print 'Warning - no workers'   
                TaskTree.add_to_sq(sq[0],sq[1])              # Put the task back in the queue
                break

    def process_approval(self,msg):
        child = TaskTree[msg['super_task_id']]#might be incorrectly using supertaskid
        if(msg['super_approve'] == False): #rejected, set worker and task idle
            child.status = 'idle'
            wm.W.complete(child.wid,False)
            msg['mode']='idle'
            msg['WID']=child.wid
            send_task(msg)
            TaskTree.add_to_q(0,child.id)
        else:                            #approved 
            child.status = 'approved'
            if(child.type=='leaf'):#release leaf to idle & complete
                child.sapify_leaf()
                wm.W.complete(child.wid,True)
                msg['mode']='idle'
                msg['WID']=child.wid
                send_task(msg)
                #tell parent to try to sap
                TaskTree.update_sap(child)
            else:                         #tell brancher to go super   
                msg['super_mode']='idle'
                msg['mode']='super'
                msg['WID']=child.wid
                TaskTree.generate_branches(child.id) #generate branches of worker
                send_task(msg)

        if(TaskTree.is_root(child.id) is False):
            parent = TaskTree[msg['TID']]
            if(TaskTree.finished_supervision(parent.id)):
                parent.state = 'sap' #is this too early? we want someone to come along adn sap this now     
                wm.W.complete(parent.wid,False)
                msg['mode']='idle'
                msg['WID']=parent.wid
                send_task(msg)
            
    def send_msg(self,msg):
        self.write_message(tornado.escape.json_encode(msg))

    def logout_callback(self,msg):
        self.close()
        
    def idle_callback(self,msg):
        print "idle callback"
        
    def ready_callback(self,msg):
        if(TaskTree[msg['TID']].status=='sap'):
            mode = 'sap'
        else:
            mode = TaskTree[msg['TID']].type

            print "pref:",msg['preference']
        if(msg['preference'] == "accept"):            
            # #increase idle time
            # mins = (msg['time_end']-msg['time_start']).total_seconds() / float(60)
            # print "adding idle mins:", mins
            # wm.W.addIdleTime(self.workerId,mins)
            
            if(mode == 'sap'):
                TaskTree[msg['TID']].add_wid(self.workerId)
            else:
                TaskTree[msg['TID']].add_sapwid(self.workerId)

            print "ACCEPTED, mode:",mode
            msg['mode']=mode           
            send_task(msg)
            
        else:
            print "declined"
            msg['mode']='idle'
            send_task(msg)
            if(mode=='sap'):
                TaskTree.add_to_sq(0,msg['TID'])
            else:
                TaskTree.add_to_q(0,msg['TID'])
                
            wm.W.complete(self.workerId,None) 

        print "ready callback" #???

    def task_callback(self,msg):
        if(TaskTree.is_root(msg['TID']) is True):
            TaskTree[msg['TID']].status = 'sap'
            TaskTree[msg['TID']].add_wid(self.workerId)
            msg['super_approve']=True
            msg['super_task_id']=msg['TID']
            TaskTree.save_results(msg)
            self.process_approval(msg)
            
        elif(TaskTree[msg['TID']].status != 'sap'):
            TaskTree.ask_approval(msg)     # send msg to parent to approve
            TaskTree.save_results(msg)     # save results of the task       
        else:
            TaskTree.process_sap(msg)        
            wm.W.complete(child.wid,True)

        #keep this around... maybe
        #if(task_approved):
            #increase active time
            # mins = (msg['time_end']-msg['time_start']).total_seconds() / float(60)
            # print "adding active mins:", mins
            # wm.W.addActiveTime(self.workerId,mins)       
        
        self.shake_tree()
        self.shake_tree_sap()
        
        print "task callback" 

    def super_callback(self,msg):

        self.process_approval(msg)
                        
        self.shake_tree(mode='super')

    def select_callback(self,msg):
        wm.W.set_type(self.workerId,msg['preference'])
        self.preference = msg['preference']
        self.send_msg(tms.new_msg(mode="idle",WID=self.workerId,TID=""))#fill in params more completely
        print "select callback shake starts"
        len = TaskTree.get_q_len()                  # Tasks available ?
        self.shake_tree()                       # Look to match more work and tasks
        self.shake_tree_sap()
        print "select callback shake returns"
    
    def __init__(self, application, request, **kwargs):
        super(WebSocketHandler, self).__init__(application, request, **kwargs)
        self.workerId = self.get_argument("workerId",None)
        self.hitId = self.get_argument("hitId",None)
        self.callback = {"select"   : self.select_callback,
                         "idle"     : self.idle_callback,
                         "ready"    : self.ready_callback,
                         "branch"   : self.task_callback,
                         "leaf"     : self.task_callback,
                         "sap"      : self.task_callback,
                         "super"    : self.super_callback,
                         "logout"   : self.logout_callback,
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
        # msg['time_start'] = self.time_stamp
        # msg['time_end'] = datetime.utcnow()
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
        
        #abandon current task:
        TID = wm.W.get_TID(self.workerId)
        if(TID is not False):
            print "aborting task: ",TID
            
            if(TaskTree[TID].status=='sap'):
                TaskTree.add_to_sq(0,TID)
            else:                
                TaskTree.add_to_q(0,TID)
            wm.W.complete(self.workerId,False)
            #NOTE!!! may want to add dynamically changing priority
            
        t_amt.delete_amt_hit(self.hitId)
        
        wm.W.logout(self.workerId)

