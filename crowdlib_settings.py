#!/usr/local/bin/python2.7

from crowdlib import settings as cls
import keys
import os

# SERVICE TYPE
cls.service_type = "sandbox"  # REQUIRED; must be either "sandbox" or "production"

# # AWS ACCOUNT INFO
cls.aws_account_id  = keys.aws_account_id                  
cls.aws_account_key = keys.aws_account_key 

# DIRECTORY FOR CROWDLIB DATABASE
cls.db_dir = os.path.abspath(os.path.expanduser("~/.crowdlib_data/"))  # Optional; this is the default

# DEFAULT PARAMETERS used when creating HITs
cls.default_autopay_delay              = 60*60*48   # Optional; auto-pay after 48 hours; default is 7 days
cls.default_reward                     = 0.01       # Optional; no default (i.e., specify each time)
cls.default_lifetime                   = 60*60*24*7 # Optional; available up to 1 week (same as default)
cls.default_max_assignments            = 1          # Optional; 1 judgment (same as default)
cls.default_time_limit                 = 60*30      # Optional; auto-return after 30 mins (same as default)
cls.default_qualification_requirements = ()         # Optional; default is no qualification requirement
cls.default_requester_annotation       = ""         # Optional; default is no requester annotation
cls.default_keywords                   = ()         # Optional; default is no keywords
