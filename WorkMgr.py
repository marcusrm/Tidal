## WORKER MANAGER

# Provided Methods:
# See WorkMGr_Help.txt for help on using work manager
# Run W.api() to see all APIs offered

# Dev inputs
DEVMODE=False		# RUN STUFF IN SANDBOX
DUMMYCODE=False		# RUN CODE AT END OF LIBRARY


# Import Required Files
import os,sys
os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
sys.path.append("./TaskMgr/")
import copy				# For deep copying objects
import tidal_amt as AMT # Using grant_bonus,post_hit,pay_worker
#import TaskMgr as TM	# Sending logout to user
import tidal_msg		# Create Socket Message 
import sqlite3
import pickle
from Queue import PriorityQueue


from pdb import set_trace as brk		# Breakpoint
	
# Defining Global Worker Variables
w={}				# Worker Dictionary of Objects
wDBcon={}			# Worker Database Connection Object

# Defining Self Contained Class
class W(object):
	# Class Attributes- Lists contain general info about pool 
	Loffline=[] 	# List of all offline workers
	Lonline= []		# List of all online workers
	Lidle=	 []		# List of all online idle workers
	Lleaf=	 []     # List of all online leafers  
	Lbranch= []		# List of all online branchers
	Lsap=	 []		# List of all online sappers
	
	# Class Attributes- Pay Related
	wIdleThres=10		# Idle Time Threshold in minutes
	wIdlePay=0.20		# Idle Time Pay in dollars $$$$
	wTaskPay=0.50		# Pay amount per task $$$$
	
	# Priority Queues of leafers (priority,WID)
	LQueue={'branch':PriorityQueue(),'leaf':PriorityQueue(),'sap':PriorityQueue()}
	
	# Initialization
	def __init__(self,WID):
		self.WID=WID			# Worker ID-> 			WORKER ID
		self.HID=False			# Hit ID->		CURRENT AMT HIT ID		# RESET
		self.TID=False			# NA or assigned TID->	Current TID						# RESET
		self.status='offline' 	# online, offline->    	WORKER STATUS 					# RESET
		self.type=None			# leaf, sap, branch-> 	WORKER TYPE						# RESET
		self.Socket=False		# SockObj or None-> 	WORKER SOCKET OBJECT			# RESET
		
		
		# Profile based information
		self.PtimeIdle		=0	# Idle Time												# RESET
		self.PtimeActive	=0	# Total Time Spend										# RESET
		
		self.PmoneyEarned	=0	# Net money earned
		self.PmoneyPend		=0	# Pending amount										# RESET
		
		self.PtaskDoneCurrent=0	# Tasks done in current session							# RESET
		self.PtaskDone		=[]	# List of TIDs completed
		self.Ptaskapprove	=0	# Total number of approved tasks
		self.Ptaskreject	=0	# Total number of tasks rejected
		
		self.Pbranch		=0	# Number of Branch Tasks Done
		self.Pleaf			=0	# Number of Leaf   Tasks Done
		self.Psap			=0	# Number of Sap Tasks Done

	# Add Worker	
	@staticmethod
	def add(WID):
		global w
		WID=str(WID)
		if (W.check(WID) and (WID not in w.keys())):
			w[WID]=W(WID)			# Create Worker Instance
			W.Loffline.append(WID)	# Add worker to offline list
			W.DbUpdate(WID)			# Adding Entry To Database
			print('WrkMgr: Add Success. WID-'+str(WID))
			return True
		else:
			print('WrkMgr: Add Error-Invalid WID or WID already exists. WID-'+str(WID))
			return False
		
	# Remove Worker
	@staticmethod
	def remove(WID):
		global w
		WID=str(WID)
		if W.check(WID):
			W.Lremove(WID)		# Removing worker from all lists
			W.Loffline.remove(WID)
			if WID in w:
				W.DbDelete(WID)
				w.pop(WID,None)		# Remove from dictionary
				print('WrkMgr: Remove Success. WID-'+str(WID))
				return True
			else: 
				print('WrkMgr: Remove Error- WID doesn\' exist. WID-'+str(WID))
				return False
		else:
			print('WrkMgr: Remove Error- Invalid WID. WID-'+str(WID))
			return False
	
	# Login Worker
	@staticmethod
	def login(WID,HID=False,TYPE=None,SockObj=False):
		global w
		WID=str(WID)
		if not(W.check(WID) & W.check(TYPE)):
			print('WrkMgr: Login error: Invalid Arguments. WID-'+str(WID))
			return False
		
		if(HID==False):
			print('WrkMgr: WID-'+str(WID)+' Login Error: No Hit ID specified')
			return False

		try:
			if (WID in W.Loffline):
				if(w[WID].status!='offline'): 
					print('WrkMgr login error: worker already online. WID-'+str(WID))
					return False
			
				# Update Class lists for idle and online workers
				W.Lonline.append(WID)
				W.Loffline.remove(WID)
				W.Lidle.append(WID)
				
				# Update Socket Object for Worker
				w[WID].Socket=SockObj
				
				# Associate WID with HID for current Login session
				w[WID].HID=HID
				
				# Update specific worker and Class list
				w[WID].status='online'
				w[WID].TID=False
				w[WID].type=None
				
				W.DbUpdate(WID)
				print('WrkMgr: Login Success. WID-'+str(WID))
				return True
			else:
				print('WrkMgr: Login Error. WID Doesn\'t exist. WID-'+str(WID))
				return False
		except:
			print('WrkMgr: Login Error. Unknown Exception WID-'+str(WID))
			return False

	# Logout Worker
	@staticmethod
	def logout(WID):
		global w
		WID=str(WID)
		try:
			if w[WID].PtaskDoneCurrent>0:
				AMT.pay_worker(w[WID].HID)				# Paying Worker Base HIT Amount only if atleast one task is done
				try:
					if(w[WID].PmoneyPend >= 0.01):		# Pay pending amount
						AMT.grant_bonus(w[WID].HID,w[WID].PmoneyPend) 	
				except:
					print "WrkMgr: logout Error. "+str(WID)+"AMT.grant_bonus error"
					return False
					
				w[WID].PmoneyEarned+=w[WID].PmoneyPend	# Incrementing net amount earned
				w[WID].PmoneyPend=0						# Clear amount earned
				print('WrkMgr: Logout: Success. Amount Paid. WID-'+str(WID) )
			else:	
				w[WID].PmoneyPend=0						# Clear amount earned
				print('WrkMgr: Logout: Success. No Amount Paid. No task done. WID-'+str(WID) )
			
			w[WID].PtaskDoneCurrent=0					# Clear Task Counter
			w[WID].TID=False							# Clear TID
			w[WID].status='offline'						# Make worker offline
			w[WID].Socket=False							# Clear Socket
			W.Lremove(WID)								# Remove From All Lists
			W.Loffline.append(WID)						# Make Worker Offline
			W.DbUpdate(WID)								# Update in Database
			
			return True
		except:
			print('WrkMgr: Logout Error. Amount Not Paid. Not Logged Out. WID-'+str(WID))
			return False
			
	# Update Current IDLE Time
	@staticmethod
	def addIdleTime(WID,TimeIdle=0):
		try:
			w[WID].PtimeIdle+=TimeIdle								# Incrementing Idle Time [minutes]
			
			# Pay only if idle greater than threshold and atleast one task done in current session
			if(w[WID].PtimeIdle>W.wIdleThres and PtaskDoneCurrent>0):	
				w[WID].PmoneyPend+=W.wIdlePay						# Increment worker's amount
				w[WID].PtimeIdle=0									# Reset Idle counter back to zero
			return True
		
		except:
			print ("WrkMgr: addIdleTime Error. WID-"+str(WID))
			return False
			
	# Update Active Time
	@staticmethod
	def addActiveTime(WID,TimeActive=0):
		try:
			[WID].PtimeActive+=TimeActive
			return True 
		except:
			print ("WrkMgr: addActiveTime Error. WID-"+str(WID))
			return False
			
	# Assign Task to Worker
	@staticmethod
	def assign(TYPE,TID):
		global w
		TYPE=str(TYPE)
		TID=str(TID)

		# Remove worker from Idle List
		try:
			# Get an idle worker 
			WIDassign=W.LQPop(TYPE=TYPE)
			
			# If no leafer available, return idle brancher
			if WIDassign==False and TYPE=='leaf':
				WIDassign=W.LQPop(TYPE='branch')
			
			# Check if Worker Returned
			if WIDassign==False:
				print("WrkMgr: assign warning. no free worker available")
				return False
			
			W.Lidle.remove(WIDassign)
			w[WIDassign].TID=TID
			
			W.DbUpdate(WIDassign)
			print('WrkMgr: assign successful. WID-'+str(WIDassign))
			return WIDassign
		except:
			print('WrkMgr: worker assign error. TID-'+str(TID))
			return False

	# Assign Task to Worker
	@staticmethod
	def complete(WID,TaskAccepted=True):					# TaskAccepted=True,None,False	None-Just Release worker
		global w
		WID=str(WID)
		
		if (w[WID].TID==False):
			print('WrkMgr: complete warning- Worker has no task assigned to be indicated as complete. WID-'+str(WID))
			return False
		
		# Add worker back to Idle List
		try:
			# Task History Based- Don't add to statistics if None
			if TaskAccepted!=None:							# Don't increment if no task assigned
				w[WID].PtaskDone.append(w[WID].TID);		# Save Task History of worker
				w[WID].PtaskDoneCurrent+=1					# Increment tasks done in  current session
			w[WID].TID=False								# Reset TID label for worker
			
			# Acceptance of Task
			if TaskAccepted==True:
				w[WID].Ptaskapprove	+=1						# Increment worker's total number of approved tasks
				w[WID].PmoneyPend	+=W.wTaskPay			# Pay for the task
				
				# Increment Points
				type=w[WID].type
				if type=='leaf':
					w[WID].Pleaf+=1
				elif type=='branch':
					w[WID].Pbranch+=1
				elif type=='sap':
					w[WID].Psap+=1
					
			# Rejection
			elif TaskAccepted==False:
				w[WID].Ptaskreject	+=1						# Increment worker's total number of rejected tasks
		
			# Decide whether to retain worker
			if(W.WrkPoolMgmt(WID)):							# Automatically logs out current worker/adds new workers if required
				print('WrkMgr: complete- success. Worker logout initiated. WID-'+str(WID))
				return True
				
			# Add current Worker back to Priority Lists and Idle Lists
			if WID not in W.Lidle:
				W.Lidle.append(WID)							# Add to idle list
				W.DbUpdate(WID)								# Update to database
				W.LQpush(WID)								# Push worker back into Priority Queue
				print('WrkMgr: complete- success. Worker added back to pool. WID-'+str(WID))
				return True
			else:
				print('WrkMgr: complete- failure. Worker already in pool. Data mismatch. WID-'+str(WID))
				return False
				
		except:
			print('WrkMgr: worker Complete error. Error reporting task completion. WID-'+str(WID))
			return False
	
	# Decides whether to get more workers or let go of current worker 
	@staticmethod
	def WrkPoolMgmt(CurrWID=False):
		if CurrWID==False:
			print('WrkMgr: PoolMgmt- No current worker specified to decide on whether to retain.')
			return False
		
		# Contact Tree to find info on stuff
		try:
			TaskInfo=tree.TaskTree.get_task_count()							# Returns Dict of all task types
			TaskNum=TaskInfo['branch']+TaskInfo['leaf']+TaskInfo['sap']		# Add all tasks
			WrkNum=len(W.Lonline)											# Find online workers
			
			# LESS WORKERS PRESENT. PUT OUT HITS
			if(TaskNum> (2*WrkNum)):		
				HITnum=int((TaskNum - (2*WrkNum))/2)
				AMT.post_hit(HITnum)
			# TOO MANY WORKERS PRESENT. LOGOUT THE CURRENT WORKER
			if(TaskNum< (0.5*WrkNum)):	
				msg=tidal_msg.send_msg(mode='logout')						# Forcing User to logout
				#TM.send_task(msg)											# Send logout command
				return True													# return that current user is logged out
		except:
			print('WrkMgr: PoolMgmt- Pool Mgmt didn\'t execute. No harm done')
			return False
		
	# Return Current Task ID
	@staticmethod
	def get_TID(WID):
		return w[WID].TID
		
	# To Set Worker Type='leaf','branch','sap'
	@staticmethod
	def set_type(WID,TYPE):
		global w
		TYPE=str(TYPE)
		# Remove Worker from previous lists. Do first, ask later!! =)
		try:
			W.Lleaf.remove(WID);
		except:
			try:	
				W.Lbranch.remove(WID);
			except: 	
				try:	W.Lsap.remove(WID);
				except: pass

		try:
			if TYPE=='sap':	
				W.Lsap.append(WID)				
			elif TYPE=='branch':	
				W.Lbranch.append(WID)
			elif TYPE=='leaf':
				W.Lleaf.append(WID)
			else:
				return False
			
			# Set Worker Type 
			w[WID].type=TYPE	
			
			# Push Worker Into Queue
			W.LQpush(WID)		
			
			# Update in Database
			W.DbUpdate(WID)
			print('WrkMgr: set_type: Successfully changed. WID-'+str(WID))
			return True
		except:
			print('WrkMgr: set_type Error: Unknown Exception. WID-'+str(WID))
			return False
	
	# Returns Worker Type
	@staticmethod
	def get_type(WID):
		global w
		try:
			return w[WID].type
		except:
			print('WrkMgr: get_type Error- Worker Doesn\'t Exist')
			return False

	# To store socket object to worker
	@staticmethod
	def set_socket(WID,SockObj):
		print('-'*50)
		global w
		try:
			w[WID].Socket=SockObj
			W.DbUpdate(WID)
			print('WrkMgr: set_socket- success')
			return True
		except:
			print('WrkMgr: set_socket- Failure')
			return False
			
	# To retrieve socket object to worker
	@staticmethod
	def get_socket(WID):
		global w
		return w[WID].Socket
	
	# Initialize Database & 'w' dictionary
	@staticmethod
	def WMinit(WipeDB=False,Sandbox=DEVMODE):
		global w, wDBcon
		# Connect to DB: if doesn't exist, create one
		try:
			# Connect to Database
			if(Sandbox):
				wDBcon=sqlite3.connect('static/wDBsandbox.db')
			else:
				wDBcon=sqlite3.connect('static/wDBdeploy.db')

			# Setup Table and parameters of connection
			cmd='create table if not exists WM(WID text primary key,OBJECT text)' 	# WORKER TABLE
			cmd1='create table if not exists WMList(Type text primary key,OBJECT text)' 	# WORKER TABLE
			wDBcon.execute(cmd)
			wDBcon.execute(cmd1)
			
			wDBcon.row_factory=sqlite3.Row
			wDBcon.text_factory=str
			wDBcon.isolation_level=None
			
			# Wipe Database Clean and add create new table
			if(WipeDB): 			
				WipeDB=raw_input("WorkMgr: Are you sure you want to wipe DB? Enter t to wipe: ")
				if(WipeDB=='t'):
					w={}
					cmd='delete from WM'
					wDBcon.execute(cmd)			
			
			
			# Load Worker Data into Working Memory
			cmd='select * from WM'
			for row in wDBcon.execute(cmd):
				WID=str(row[0])
				w[WID]=pickle.loads(row[1])
				
				# Check if previous payment unpaid
				if w[WID].PmoneyPend>0:
					try:
						AMT.pay_worker(w[WID].HID)				# Paying Worker Base HIT Amount only if atleast one task is done
						AMT.grant_bonus(w[WID].HID,w[WID].PmoneyPend) 	
						print('WrkMgr: Init- Previous amount not paid to worker. Paying to WID-'+str(WID))
					except:
						print('WrkMgr: Init- Error paying previous amount to WID-'+str(WID))
				
				# Resetting a few fields
				w[WID].HID				=False		# Hit ID->		CURRENT AMT HIT ID
				w[WID].TID				=False		# NA or assigned TID->	Current TID				
				w[WID].status			='offline' 	# online, offline->    	WORKER STATUS 			
				w[WID].type				=None		# leaf, sap, branch-> 	WORKER TYPE				
				w[WID].Socket			=False		# SockObj or None-> 	WORKER SOCKET OBJECT	
				w[WID].PtimeIdle		=0			# Idle Time										
				w[WID].PtimeActive		=0			# Total Time Spend								
				w[WID].PmoneyPend		=0			# Pending amount								
				w[WID].PtaskDoneCurrent	=0			# If Active in current session					
			
			# Check and add 'admin' entry into DB
			if 'admin' not in w:
				print('WrkMgr: Initialising Adding admin')
				W.add('admin')
			
			# Make all Users Offline
			W.Lonline=[]
			W.Loffline=w.keys()
			
			print('WrkMgr WMinit: Worker Manager Initialised and Database linked')
			return True
			
		except:
			print('WrkMgr WMinit Error: Worker Database could not be setup properly')
			return False

	# Update Worker Info in Database
	@staticmethod
	def DbUpdate(WID):
		if WID in w:
			# Database Stuff
			try:
				wdump=copy.copy(w[WID])				# Create a local copy
				wdump.Socket=False
				DBObject=pickle.dumps(wdump,protocol=2)
				cmd='insert or replace into WM values(?,?)'
				cur=wDBcon.execute(cmd,(WID,DBObject))	
			except:
				print('WrkMgr: WID-'+str(WID)+' DbUpdate Error: WORKER details not updatable')
				return False
		
			# Update Class Attributes in database
			try:
				cmd='insert or replace into WMList values(?,?)'
				cur=wDBcon.execute(cmd,('Loffline'	,pickle.dumps(W.Loffline,protocol=2)))		
				cur=wDBcon.execute(cmd,('Lonline'	,pickle.dumps(W.Lonline	,protocol=2)))		
				cur=wDBcon.execute(cmd,('Lidle'		,pickle.dumps(W.Lidle	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lleaf'		,pickle.dumps(W.Lleaf	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lbranch'	,pickle.dumps(W.Lbranch	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lsap'		,pickle.dumps(W.Lsap	,protocol=2)))		
			except:
				print('WrkMgr: WID-'+str(WID)+' DbUpdate Error: LIST details not updatable')
				return False
	
	# Delete Entry from Database 
	@staticmethod
	def DbDelete(WID):
		if WID in w:
			cmd='delete from WM where WID=?'
			wDBcon.execute(cmd,(WID,))
			
	# Priority Queue for Worker Task Deployment- Push Worker to Queue
	@staticmethod
	def LQpush(WID):
		# Get worker type
		TYPE=w[WID].type
	
		# Check if worker type set
		if TYPE==None:
			print('WrkMgr: LQpush error. '+str(WID)+' type not set')
			return False
	
		# Calculate Priority for Workers [PRIORITY CALCULATION OF WORKERS]
		if TYPE=='leaf':
			priority=w[WID].Pleaf
		elif TYPE=='branch':
			priority=w[WID].Pbranch
		elif TYPE=='sap':
			priority=w[WID].Psap
		else:
			print("WrkMgr: LQpush Error. Error pushing "+str(WID)+" into priority queue")
			return False
		
		
		# Push the worker along with the priority to the Q
		try:
			W.LQueue[TYPE].put_nowait((-priority,WID))		# Note: '-'ve sign. Lower #=Higher Priority
			return True
		except:
			print('WrkMgr Qpush Error: Push Exceptionn')
			return False
		
	# Priority Queue for Worker Task Deployment- Return from Queue
	@staticmethod
	def LQPop(TYPE):
		# Getting data back from queue
		try:
			while(not W.LQueue[TYPE].empty()):		# Check if Q empty
				wid=W.LQueue[TYPE].get_nowait()	# Check Pop the queue
				wid=str(wid[1])					
				if W.Lidle.__contains__(wid) and w[wid].type==TYPE:	# See if popped worker is idle & of same type
					return wid
			return False
		except:
			print('WrkMgr Qpop Error: unknown exception with priority queue')
			return False
			
	# Return Data to the worker's console dashboard
	@staticmethod
	def getHUD(WID):
		try:	HourlyRate=w[WID].PtimeActive/w[WID].PmoneyEarned
		except ZeroDivisionError: HourlyRate=0
		
		try:	TaskApprRate=w[WID].Ptaskapprove/len(w[WID].PtaskDone)
		except ZeroDivisionError: TaskApprRate='NA'
		
		msg={
		'ThisSessionEarned'		:w[WID].PmoneyPend,
		'ThisSessionTasks'		:w[WID].PtaskDoneCurrent,
		'OverallEarned'			:w[WID].PmoneyEarned,
		'OverallBranchTasks'	:w[WID].Pbranch,
		'OverallLeafTasks'		:w[WID].Pleaf,
		'OverallSapTasks'		:w[WID].Psap,
		'OverallHourlyRate'		:HourlyRate,
		'OverallApprovalRate'	:TaskApprRate}
		return msg
			
	# Check if Worker Exists In Database
	@staticmethod
	def WIDexist(WID):
		if WID in w:
			return True
		else:
			return False

	# Check WID for special characters
	@staticmethod
	def check(WID):
		WID=str(WID)
		return WID.isalnum()
		
	# Remove WID From All Lists
	@staticmethod
	def Lremove(WID):
		if W.check(WID):
			try: W.Lidle.remove(WID);
			except:	pass
			
			try: W.Lonline.remove(WID);
			except:	pass
			
			try: W.Lbranch.remove(WID);
			except: pass
			
			try: W.Lsap.remove(WID);
			except: pass
			
			try: W.Lleaf.remove(WID);
			except: pass
			
			try: W.Loffline.remove(WID);
			except: pass
			
	# To display details of worker
	@staticmethod
	def disp(WID):
		print('WID: '+str(w[WID].WID))
		print('Status: '+str(w[WID].status))
		print('TID: '+str(w[WID].TID))
		print('HID: '+str(w[WID].HID))
		print('Type:'+str(w[WID].type))
		
		print('Total Approvals: '+str(w[WID].Ptaskapprove))
		print('Total Rejects: '+str(w[WID].Ptaskreject))
		print('Total Tasks: '+str(len(w[WID].PtaskDone)))
		print('Current Streak: '+str(w[WID].PtaskDoneCurrent))
		print('Task History:'+str(w[WID].PtaskDone))

		print('Profile Points:')
		print('    Branch:'+str(w[WID].Pbranch))
		print('    Leaf:  '+str(w[WID].Pleaf))
		print('    Sap:   '+str(w[WID].Psap)+'\n')
		print('Socket:'+str(w[WID].Socket))
		
	# To display List Content
	@staticmethod
	def displ():
		print('Online List')
		print(W.Lonline)
		print('\n\n\n')
		
		print('Offline List')
		print(W.Loffline)
		print('\n\n\n')
		
		print('Idle List')
		print(W.Lidle)
		print('\n\n\n')
		
		print('Branch List')
		print(W.Lbranch)
		print('\n\n\n')
		
		print('Leaf List')
		print(W.Lleaf)
		print('\n\n\n')
		
		print('Sap List')
		print(W.Lsap)
		print('\n\n\n')
		
	# List All Class Methods and Attributes
	@staticmethod
	def api():
		try:
			a=[a for a in dir(W) if not(a.startswith('__') and a.endswith('__'))]
			print(a)
		except:
			print("WrkMgr APIs: Unknown Error")

#################### INITIALIZE THE WORK MANAGER ##########################
#W.WMinit()		# Automatically adds the 'admin' to pool


#################### DEVELOPER SPACE ######################################
if(DEVMODE==True and DUMMYCODE==True):			# Add Dummy Workers To Pool
	type=['leaf','branch','sap']
	W.add('0');	W.add('1'); W.add('2');
	W.login('1','aid1'); W.login('2','aid2');
	W.set_type('1','leaf'); W.set_type('2','branch')
	Assigned1=W.assign('leaf','TID1');  Assigned2=W.assign('branch','TID2'); 
	W.complete(Assigned1,True);			W.complete(Assigned2,False);
	W.logout(Assigned1);				W.logout(Assigned2);
	W.displ() 