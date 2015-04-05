# WorkPool Manager

# Methods:
# W.add(WID): 		returns a True/False and requires input of Worker ID(WID) as string. Returns True/False
# W.delete(WID): 	deletes the WID from the pool/database. Returns True/False
# W.login(WID): 	logs in the respective WID. Returns True/False
# W.logout(WID): 	logs out the respective WID. Returns True/False
# W.assign(TID,Type): Assigns the Task ID (TID) to a given Type ("leaf","branch","sap"). Returns WID/False
# W.print(WID): 	prints all info about worker

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
		self.WID=WID
		self.status='offline' 	# online, offline->    	WORKER STATUS
		self.type='leaf'		# leaf, sap, branch-> 	WORKER TYPE
		self.TID='NA'			# NA or assigned TID->	WORKER TASK STATUS
		
		# Profile based information
		TaskHist=[]				# List of all tasks done
		Pt={'branch':0,'leaf':0,'sap':0}
		Others={}			
		self.prof={'TaskHist':TaskHist,'Pt':Pt,'Others':Others}
	
	# Check WID for special characters
	def check(WID):
		WID=str(WID)
		return WID.isalnum()
			
	# Remove WID From Lists
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
			
	# Add Worker
	def add(WID):
		global w
		WID=str(WID)
		if W.check(WID):
			w[WID]=W(WID)			# Add to pool
			W.Loffline.append(WID)
			return True
		else:
			return False

	# Remove Worker
	def delete(WID):
		global w
		WID=str(WID)
		if W.check(WID):
			W.Lremove(WID)		# Removing worker from all lists
			if WID in w:
				w.pop(WID,None)		# Remove from pool
				return True
			else: 
				return False
		else:
			return False
	
	# Login Worker
	def login(WID,TYPE='default'):
		global w
		WID=str(WID)
		if(TYPE=='default'):
			print('Worker Login Type defaulted: leaf')
			TYPE='leaf'
			
		try:
			if W.check(WID) & W.check(TYPE):
				# Update Class lists for idle and online workers
				W.Lonline.append(WID)
				W.Loffline.remove(WID)
				W.Lidle.append(WID)
				
				# Update specific worker and Class list
				w[WID].status='online'
				w[WID].TID='NA'
				if TYPE=='sap':
					w[WID].type=TYPE
					W.Lsap.append(WID)
				elif TYPE=='branch':	
					w[WID].type='branch'
					W.Lbranch.append(WID)
				elif TYPE=='leaf':
					w[WID].type='leaf'
					W.Lleaf.append(WID)
				else:
					return False
					
				return True
			else:
				print('Check WID')
				return False
		except:
			print('Login Error')
			return False

	# Logout Worker
	def logout(WID,TYPE):
		global w
		WID=str(WID)
		if W.check(WID) & W.check(TYPE):
			w[WID].status='offline'
			W.Lremove(WID)
			return True
		else:
			return False
	
	
	# Assign Task to Worker
	def assign(TYPE,TID):
		global w
		TYPE=str(TYPE)
		TID=str(TID)

		# Remove worker from Idle List
		try:
			if TYPE=='branch':
				WID_list=list(set(W.Lidle) & set(W.Lbranch))
			elif TYPE=='leaf':
				WID_list=list(set(W.Lidle) & set(W.Lleaf))
			elif TYPE=='sap':
				WID_list=list(set(W.Lidle) & set(W.Lsap))
			print(WID_list)
			if len(WID_list):
				WIDassign=WID_list[0]
				W.Lidle.remove(WIDassign)
				w[WIDassign].TID=TID
				return WIDassign
			else:
				return False
		except:
			print('Error')
			return False

	# Assign Task to Worker
	def complete(WID):
		global w
		WID=str(WID)

		# Add worker to Idle List
		try:
			w[WID].TID='NA'				# Set worker object attributes
			if WID not in W.Lidle:
				W.Lidle.append(WID)		# Add to idle list
				return True
		except:
			return False
			
	# To display details of worker
	def disp(self):
		print('Status: '+str(self.status))
		print('WID: '+str(self.WID))
		print('TID: '+str(self.TID))
		print('Type:'+str(self.type))
		
	# To display List Content
	def dispL():
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
		
##########################################################################
# Initializing the Worker Dictionary
w={}
WID='1'
W.add(WID)