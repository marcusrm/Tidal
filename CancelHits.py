import crowdlib as cl,crowdlib_settings,time,os
from crowdlib import settings as cls

import keys
cls.aws_account_id  = keys.aws_account_id        # REQUIRED; "Access Key ID" from AWS
cls.aws_account_key = keys.aws_account_key 		# REQUIRED; "Secret Access Key" from AWS

def cancel():
	cl.set_all_hits_unavailable()
	print("All HITs cancelled")

if __name__=='__main__':
	cancel()
