#!/usr/local/bin/python2.7
import crowdlib as cl 
import crowdlib_settings
import time
import uuid
import tidal_settings as ts
import sqlite3
import os 

BASE_REWARD = 0.05
TIME_LIMIT = 3600
KEYWORDS = ["tidal"]
AUTOPAY_DELAY = 3600*.5

PUB_URL = "https://crowd.ecn.purdue.edu"+ts.URL_PREFIX+"/wlogin"
#PUB_URL = "http://127.0.0.1:"+str(ts.PORT)+ts.URL_PREFIX+"/wlogin"

MAX_ASSIGNMENTS = 1
LIFETIME = 3600*10

hit_type = cl.create_hit_type(title = "Join the rising tide!", 
                              description = "Participate in an experimental \
                              crowd-working platform similar to AMT!",
                              reward = BASE_REWARD,
                              time_limit = TIME_LIMIT,
                              keywords = KEYWORDS, 
                              autopay_delay = AUTOPAY_DELAY)
def init_amt_task_db():   
    db_missing = not os.path.exists(ts.AMT_TASK_DB)
    if(db_missing):
        conn = sqlite3.connect(ts.AMT_TASK_DB)
        c = conn.cursor()
        with open(ts.AMT_TASK_SCHEMA,'rt') as f:
            schema = f.read()
        c.executescript(schema)
        conn.close()

def store_amt_task(amt_task_id,hit):
    conn = sqlite3.connect(ts.AMT_TASK_DB)
    c = conn.cursor()
    c.execute('INSERT INTO amt_task (amt_task_id,hitId,assignmentId)'\
              'values (?,?,?)',[amt_task_id,hit.id,""])
    conn.commit()
    conn.close()

def delete_amt_task():
    pass

def set_amt_task_pending():
    pass

def grant_bonus(assignmentId, task_id, amount):
    assignment = cl.get_assignment(assignmentId)
    if(assignment != None):
        assignment.grant_bonus(amount,"payment for Tidal task (#"+task_id+")")
    
def pay_worker(assignmentId):
    assignment = cl.get_assignment(assignmentId)
    if(assignment != None and assignment.is_final() and
       assignment.is_paid() is False):
        assignment.approve()
    
def post_hit(n_tasks):

    amt_task_id = []
    hit = []
    for t in range(0,n_tasks):
        amt_task_id.append((uuid.uuid4().hex)[0:6])
        
    # Create a HIT type, with the title and description for this group of HITs.
    # Post a HIT.
    for t in amt_task_id:
        hit = hit_type.create_hit(url = PUB_URL + "?amt_task_id=" + t,
                                       height = 500,
                                       max_assignments = MAX_ASSIGNMENTS,
                                       lifetime = LIFETIME,
                                  )
               
        print "hit posted to URL: " , PUB_URL + "?amt_task_id=" + t
        store_amt_task(t,hit)

            
def cancel_hits():
    cl.set_all_hits_unavailable()
    print "hits cancelled!"

def report():
    print "oops"

