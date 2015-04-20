## WORKER MANAGER

# Provided Methods:
# W.add(WID): 		returns a True/False and requires input of Worker ID(WID) as string.
# W.remove(WID): 	removes the WID from the pool/database. Returns True/False
# W.login(WID): 	logs in the respective WID. Returns True/False
# W.logout(WID): 	logs out the respective WID. Returns True/False
# W.assign(TID,Type): Assigns the Task ID (TID) to a given Type ("leaf","branch","sap").
# W.print(WID): 	prints all info about worker

# Import Required Files
from tidal_amt import grant_bonus,post_hit,pay_worker

# Defining Global Worker Dictionary
w={}

# Defining Self Contained Class
class W(object):
	# Class Attributes
	Loffline=[] 	# List of all offline workers
	Lonline=[]		# List of all online workers
	Lidle=[]		# List of all online idle workers
	Lleaf=[]        # List of all online leafers  
	Lbranch=[]		# List of all online branchers
	Lsap=[]			# List of all online sappers
 
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
			w[WID]=W(WID)			# Add to pool
			W.Loffline.append(WID)
			print('WrkMgr: WID-'+str(WID)+' Add: Success')
			return True
		else:
			print('WrkMgr: WID-'+str(WID)+' Add Error: Invalid WID')
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
				w.pop(WID,None)		# Remove from database
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
			#### PAY THE WORKER- RJ API HERE ####
			#### IF PAY DONE, reset amount earned #####
			w[WID].status='offline'
			w[WID].Socket=False
			W.Lremove(WID)
			w[WID].AmountEarned=0
			print('WrkMgr: WID-'+str(WID)+' Logout: Success. AMT Paid: '+str(w[WID].AmountEarned))
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
			elif TYPE=='leaf':
				WID_list=list(set(W.Lidle) & set(W.Lleaf))
			elif TYPE=='sap':
				WID_list=list(set(W.Lidle) & set(W.Lsap))
				
			if len(WID_list):
				WIDassign=WID_list[0]
				W.Lidle.remove(WIDassign)
				w[WIDassign].TID=TID
				return WIDassign
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
				return True
		except:
			return False
		
	# Add Task Pending Approval to Worker
	@staticmethod
	def pending(WID,TID,AmountPay=0):
		pass
		
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
		
	# To store socket object to worker
	@staticmethod
	def set_socket(WID,SockObj):
		global w
		w[WID].Socket=SockObj
		
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
	
	# Check if Worker Exists
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
			
	# Remove WID From Lists
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
##########################################################################
