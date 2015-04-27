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

MAX_ASSIGNMENTS = 1
LIFETIME = 3600*10

hit_type = cl.create_hit_type(title = "Join the rising tide!", 
                              description = "Participate in an experimental \
                              crowd-working platform similar to AMT!",
                              reward = BASE_REWARD,
                              time_limit = TIME_LIMIT,
                              keywords = KEYWORDS, 
                              autopay_delay = AUTOPAY_DELAY)
def init_amt_hit_db():   
    db_missing = not os.path.exists(ts.AMT_HIT_DB)
    if(db_missing):
        conn = sqlite3.connect(ts.AMT_HIT_DB)
        c = conn.cursor()
        with open(ts.AMT_HIT_SCHEMA,'rt') as f:
            schema = f.read()
        c.executescript(schema)
        conn.close()

def hit_exists(hitId):
    conn = sqlite3.connect(ts.AMT_HIT_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM amt_hit where hitId = ?',
              [hitId])
    query_result = c.fetchone()
    conn.close()
    if(query_result is None):
        return False
    else:
        return True
    
def get_hit(hitId):
    if(hit_exists):
        return cl.get_hit(hitId)
    else:
        return None
    
def get_assignment(assignmentId):
    return cl.get_assignment(assignmentId)
        
def store_amt_hit(hit):
    print "hitid",hit.id
    conn = sqlite3.connect(ts.AMT_HIT_DB)
    c = conn.cursor()
    c.execute('INSERT INTO amt_hit (hitId) values (?)',[hit.id])
    conn.commit()
    conn.close()

def delete_amt_hit(hitId):
    conn = sqlite3.connect(ts.AMT_HIT_DB)
    c = conn.cursor()
    c.execute('DELETE FROM amt_hit where hitId = ?',[hitId])
    conn.commit()
    conn.close()

def grant_bonus(assignmentId, amount):
    assignment = cl.get_assignment(assignmentId)
    if(assignment != None):
        assignment.grant_bonus(amount,"payment for Tidal task (#"+assignmentId+")")
    
def pay_worker(assignmentId):
    assignment = cl.get_assignment(assignmentId)
    if(assignment != None and assignment.is_paid() is False):
        assignment.approve()
        
    
def num_idle_amt_hits():
    conn = sqlite3.connect(ts.AMT_HIT_DB)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) from amt_hit',[])
    count = c.fetchone()[0]
    conn.commit()
    conn.close()
    return count

def post_hit(n_tasks):
    # Create a HIT type, with the title and description for this group of HITs.
    # Post a HIT.
    for i in range(0,n_tasks):
        hit = hit_type.create_hit(url = PUB_URL,
                                       height = 500,
                                       max_assignments = MAX_ASSIGNMENTS,
                                       lifetime = LIFETIME,
                                  )

        print "hit posted to URL: " , PUB_URL 
        store_amt_hit(hit)
        # #some test code:
        # print "num idle",num_idle_amt_hits()
        # print "exists (true): ",hit_exists(hit.id)
        # print "exists (false): ",hit_exists("@#RWEF")
        # delete_amt_hit(hit.id)
        # print "exists (false): ",hit_exists("@#RWEF")
        
    

            
def cancel_hits():
    cl.set_all_hits_unavailable()
    conn = sqlite3.connect(ts.AMT_HIT_DB)
    c = conn.cursor()
    c.execute('DELETE FROM amt_hit',[])
    conn.commit()
    conn.close()
    print "hits cancelled!"

def report():
    print "oops"

