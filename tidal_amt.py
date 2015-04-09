#!/usr/local/bin/python2.7
import crowdlib as cl 
import crowdlib_settings
import time
import uuid

BASE_REWARD = 0.05
TIME_LIMIT = 3600
KEYWORDS = ["categorize", "names"]
AUTOPAY_DELAY = 3600*.5

PUB_URL = "https://crowd.ecn.purdue.edu/08/"
MAX_ASSIGNMENTS = 1
LIFETIME = 3600*10

class tidal_amt():
    def post_hit(n_batches):

        for b in range(0,n_batches):
            batch_id.append((uuid.uuid4().hex)[0:6])
        
        # Create a HIT type, with the title and description for this group of HITs.
        hit_type = cl.create_hit_type(title = "Join the rising tide!", 
                                      description = "Participate in an experimental \
                                      crowd-working platform similar to AMT!",
                                      reward = BASE_REWARD,
                                      time_limit = TIME_LIMIT,
                                      keywords = KEYWORDS, 
                                      autopay_delay = AUTOPAY_DELAY)

        # Post a HIT.
        for b in batch_id:
            hit = hit_type.create_hit(url = PUB_URL + "?batch=" + b,
                                      height = 500,
                                      max_assignments = MAX_ASSIGNMENTS,
                                      lifetime = LIFETIME,
                                      )
            print "hit posted to URL: " , PUB_URL + "?batch=" + b


    def cancel_hit(hit_id):
        if(hit_id is None):
            print "no hit id given"
        else:
            
    def cancel_all_hits():
        cl.set_all_hits_unavailable()

    def report():
        
