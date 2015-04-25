## WORKER MANAGER

# Provided Methods:
# W.add(WID): 		returns a True/False and requires input of Worker ID(WID) as string.
# W.remove(WID): 	removes the WID from the pool/database. Returns True/False
# W.login(WID): 	logs in the respective WID. Returns True/False
# W.logout(WID): 	logs out the respective WID. Returns True/False
# W.assign(TID,Type): Assigns the Task ID (TID) to a given Type ("leaf","branch","sap").
# W.print(WID): 	prints all info about worker

DEVMODE=True

# Import Required Files
import tidal_amt as AMT #Using grant_bonus,post_hit,pay_worker
import sqlite3
import pickle


if(DEVMODE):
	import os,sys
	os.chdir(os.path.abspath(os.path.dirname(sys.argv[0])))
	from pdb import set_trace as brk
	
# Defining Global Worker Dictionary
w={}				# Worker Dictionary of Objects
wDBcon={}			# Worker Database Connection Object

# Defining Self Contained Class
class W(object):
	# Class Attributes
	Loffline=[] 	# List of all offline workers
	Lonline= []		# List of all online workers
	Lidle=	 []		# List of all online idle workers
	Lleaf=	 []     # List of all online leafers  
	Lbranch= []		# List of all online branchers
	Lsap=	 []		# List of all online sappers
	
	# Initialization
	def __init__(self,WID):
		self.WID=WID			# Worker ID-> 			WORKER ID
		self.AID=False			# Assignment ID->		CURRENT AMT ASSIGNMENT ID
		self.TID='NA'			# NA or assigned TID->	WORKER TASK STATUS
		self.status='offline' 	# online, offline->    	WORKER STATUS
		self.type=None			# leaf, sap, branch-> 	WORKER TYPE
		self.Socket=False		# SockObj or None-> 	WORKER SOCKET OBJECT
		self.AmountEarned=0 	# Initialize Money Earned
		
		# Profile based information
		self.TaskPend={}		# {'TID':AmountEarned,...}
		self.TaskHist=[]		# List of all tasks done
		self.Pt={'branch':0,'leaf':0,'sap':0}
		
	# Add Worker	
	@staticmethod
	def add(WID):
		global w
		WID=str(WID)
		if W.check(WID) and (WID not in w.keys()):
			w[WID]=W(WID)			# Create Worker Instance
			W.Loffline.append(WID)	# Add worker to offline list
			W.DbUpdate(WID)			# Adding Entry To Database
			print('WrkMgr: WID-'+str(WID)+' Add: Success')
			return True
		else:
			print('WrkMgr: WID-'+str(WID)+' Add Error: Invalid WID or WID already exists')
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
				print('WrkMgr: WID-'+str(WID)+' Remove: Success')
				return True
			else: 
				print('WrkMgr: WID-'+str(WID)+' Remove Error: WID doesn\' exist')
				return False
		else:
			print('WrkMgr: WID-'+str(WID)+' Remove Error: Invalid WID')
			return False
	
	# Login Worker
	@staticmethod
	def login(WID,AID=False,TYPE='leaf',SockObj=False):
		global w
		WID=str(WID)
		if not(W.check(WID) & W.check(TYPE)):
			print('WrkMgr: WID-'+str(WID)+' Login Error: Invalid Arguments')
			return False
		
		if(AID==False):
			print('WrkMgr: WID-'+str(WID)+' Login Error: No Assignment ID specified')
			return False

		try:
			if (WID in W.Loffline) and w[WID].status=='offline':
				# Update Class lists for idle and online workers
				W.Lonline.append(WID)
				W.Loffline.remove(WID)
				W.Lidle.append(WID)
				
				# Update Socket Object for Worker
				w[WID].Socket=SockObj
				
				# Associate WID with AID for current Login session
				w[WID].AID=AID
				
				# Update specific worker and Class list
				w[WID].status='online'
				w[WID].TID='NA'
				w[WID].type=TYPE
				
				if TYPE=='sap':	
					W.Lsap.append(WID)
				elif TYPE=='branch':	
					W.Lbranch.append(WID)
				elif TYPE=='leaf':
					W.Lleaf.append(WID)
				else:
					return False
				
				DbUpdate(WID)
				print('WrkMgr: WID-'+str(WID)+' Login Success')
				return True
			else:
				print('WrkMgr: WID-'+	str(WID)+' Login Error: Worker Doesn\' Exist')
				return False
		except:
			print('WrkMgr: WID-'+str(WID)+' Login Error: Unknown Exception')
			return False

	# Logout Worker
	@staticmethod
	def logout(WID):
		global w
		WID=str(WID)
		try:
			AMT.pay_worker(WID)							# Paying Worker Base HIT Amount
			# LOG WORKER OUT AMT 
			AMT.grant_bonus(WID,w[WID].AmountEarned) 
			w[WID].AmountEarned=0
			w[WID].status='offline'
			w[WID].Socket=False
			W.Lremove(WID)
			DbUpdate(WID)
			print('WrkMgr: WID-'+str(WID)+' Logout: Success. Amount Paid: '+str(w[WID].AmountEarned))
			return True
		except:
			print('WrkMgr: WID-'+str(WID)+' Logout Error: AMT Not Paid. Not Logged Out')			
			
	# Assign Task to Worker
	@staticmethod
	def assign(TYPE,TID):
		global w
		TYPE=str(TYPE)
		TID=str(TID)

		# Remove worker from Idle List
		try:
			# Returns required idle worker of requested type
			if TYPE=='branch':
				WID_list=list(set(W.Lidle) & set(W.Lbranch))
				WID_List_branch=WID_LIST
			elif TYPE=='leaf':
				WID_list=list(set(W.Lidle) & set(W.Lleaf))
			elif TYPE=='sap':
				WID_list=list(set(W.Lidle) & set(W.Lsap))
				
			# Check if specific workers available
			if len(WID_list)>0:		
				WIDassign=WID_list[0]
				W.Lidle.remove(WIDassign)
				w[WIDassign].TID=TID
				DbUpdate(WID)
				return WIDassign
				
			# If leaf task required and no leafers present, assign brancher
			elif len(WID_list_branch)>0:	
				WIDassign=WID_list_branch[0]
				W.Lidle.remove(WIDassign)
				w[WIDassign].TID=TID
				DbUpdate(WID)
				return WIDassign			# Returning Brancher
			else:
				return False
		except:
			print('Assignment Error')
			return False

	# Assign Task to Worker
	@staticmethod
	def complete(WID,TID,AmountPay=0):
		global w
		WID=str(WID)
		
		# Add worker to Idle List
		try:
			w[WID].TaskHist.append(w[WID].TID);				  # Save Task History of worker
			w[WID].TID='NA'									  # Set worker object attributes
			w[WID].AmountEarned=AmountPay+w[WID].AmountEarned # Adding to the worker's earned amount
			if WID not in W.Lidle:
				W.Lidle.append(WID)							  # Add to idle list
				DbUpdate(WID)
				return True
		except:
			return False
		
	# Add Task Pending Approval to Worker
	@staticmethod
	def pending(WID,TID,AmountPay=0):
		DbUpdate(WID)
		pass

	# To store socket object to worker
	@staticmethod
	def set_socket(WID,SockObj):
		global w
		try:
			w[WID].Socket=SockObj
			DbUpdate(WID)
			return True
		except:
			return False
			
	# To retrieve socket object to worker
	@staticmethod
	def get_socket(WID):
		global w
		return w[WID].Socket
	
	# To Set Worker Type='leaf','branch','sap'
	@staticmethod
	def set_type(WID,TYPE='leaf'):
		global w
		try:
			w[WID].type=TYPE
			DbUpdate(WID)
			print('WrkMgr: WID-'+str(WID)+' set_type: Success')
			return True
		except:
			print('WrkMgr: WID-'+str(WID)+' set_type Error: Worker Doesn\'t Exist')
			return False
	
	# Returns Worker Type
	@staticmethod
	def get_type(WID):
		global w
		try:
			return w[WID].type
		except:
			print('WrkMgr: WID-'+str(WID)+' get_type Error: Worker Doesn\'t Exist')
			return False
		
	# Initialize Database & 'w' dictionary
	@staticmethod
	def WMinit(WipeDB=False,Sandbox=DEVMODE):
		global w, wDBcon
		# Connect to DB: if doesn't exist, create one
		try:
			# Connect to Database
			if(Sandbox):
				wDBcon=sqlite3.connect('wDB_sandbox.db')
			else:
				wDBcon=sqlite3.connect('wDB_deploy.db')
			
			# Setup Table and parameters of connection
			cmd='create table if not exists WM(WID string primary key,OBJECT)' 	# WORKER TABLE
			wDBcon.execute(cmd)
			wDBcon.row_factory=sqlite3.Row
			wDBcon.text_factory=str
			wDBcon.isolation_level=None
			
			# Wipe Database Clean and add create new table
			if(WipeDB): 			
				WipeDB=raw_input("WorkMgr: Are you sure you want to wipe DB? Enter True to wipe: ")
				if(WipeDB==True):
					cmd='delete from WM'
					wDBcon.execute(cmd)			
			
			
			# Load Worker Data into Working Memory
			cmd='select * from WM'
			for row in wDBcon.execute(cmd):
				w[row[0]]=pickle.loads(row[1])
			W.Loffline=[]
			# Check and add 'admin' entry into DB
			if 'admin' not in w:
				W.add('admin')
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
				DBObject=pickle.dumps(w[WID],protocol=2)
				cmd='insert or replace into WM values(?,?)'
				cur=wDBcon.execute(cmd,(WID,DBObject))		
			except:
				print('WrkMgr: WID-'+str(WID)+' DbUpdate Error: Worker details not updatable')
				return False
		
		# Update Class Attributes in database
			try:
				DBObject=pickle.dumps(w[WID],protocol=2)
				cmd='insert or replace into WMList values(?,?)'
				cur=wDBcon.execute(cmd,('Loffline'	,pickle.dumps(W.Loffline,protocol=2)))		
				cur=wDBcon.execute(cmd,('Lonline'	,pickle.dumps(W.Lonline	,protocol=2)))		
				cur=wDBcon.execute(cmd,('Lidle'		,pickle.dumps(W.Lidle	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lleaf'		,pickle.dumps(W.Lleaf	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lbranch'	,pickle.dumps(W.Lbranch	,protocol=2)))
				cur=wDBcon.execute(cmd,('Lsap'		,pickle.dumps(W.Lsap	,protocol=2)))		
			except:
				print('WrkMgr: WID-'+str(WID)+' DbUpdate Error: Worker details not updatable')
				return False
	
	# Delete Entry from Database
	@staticmethod
	def DbDelete(WID):
		if WID in w:
			cmd='delete from WM where WID=?'
			wDBcon.execute(cmd,(WID,))

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
			if WID in W.Lidle:
				W.Lidle.remove(WID)
			if WID in W.Lonline:
				W.Lonline.remove(WID)
			if WID in W.Lbranch:
				W.Lbranch.remove(WID)
			if WID in W.Lsap:
				W.Lsap.remove(WID)
			if WID in W.Lleaf:
				W.Lleaf.remove(WID)
			if WID not in W.Loffline:
				W.Loffline.append(WID);
			w[WID].type=None
	
	# To display details of worker
	@staticmethod
	def disp(WID):
		print('WID: '+str(w[WID].WID))
		print('Status: '+str(w[WID].status))
		print('TID: '+str(w[WID].TID))
		print('Type:'+str(w[WID].type))
		print('Task History:'+str(w[WID].TaskHist))
		print('SocketID:'+str(w[WID].Socket))
		print('Profile Points:')
		print('    Branch:'+str(w[WID].Pt['branch']))
		print('    Leaf:  '+str(w[WID].Pt['leaf']))
		print('    Sap:   '+str(w[WID].Pt['sap'])+'\n\n')
		
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
	def APIs():
		a=[a for a in dir(W) if not(a.startswith('__') and a.endswith('__'))]
		for x in a:
			print(a)
	
##########################################################################
W.WMinit()		# Automatically adds the 'admin' to pool
if(DEVMODE==True):
	for i in xrange(20):
		W.add(str(i))
		if i%3==0:
			W.login(str(i),'AID:'+str(i))