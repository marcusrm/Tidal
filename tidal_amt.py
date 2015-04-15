#!/usr/local/bin/python2.7
import crowdlib as cl 
import crowdlib_settings
import time
import uuid
import tidal_settings as ts

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

def post_hit(n_tasks):

    amt_task_id = []
    hit = []
    for t in range(0,n_tasks):
        amt_task_id.append((uuid.uuid4().hex)[0:6])
        
        # Create a HIT type, with the title and description for this group of HITs.
        
        # Post a HIT.
    for t in amt_task_id:
        hit.append(hit_type.create_hit(url = PUB_URL + "?amt_task_id=" + t,
                                       height = 500,
                                       max_assignments = MAX_ASSIGNMENTS,
                                       lifetime = LIFETIME,
                                )
               )
        print "hit posted to URL: " , PUB_URL + "?amt_task_id=" + t         

    return dict(zip(amt_task_id,hit))

            
def cancel_hits():
    cl.set_all_hits_unavailable()
    print "hits cancelled!"

def report():
    print "oops"

