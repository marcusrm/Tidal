# Define a node to represent a task here
import tidal_msg as tms
import TaskMgr as tm
import copy
class Node:
	def __init__(self,tid,parent):
		#ID is a unique key used to store the nodes as a dictionary
		self.__tid 		= tid
		# Parent of this node 
		self.__parent = parent
		#List of dict keys for the dict stored in the tree class
		self.__children = [] 
		#Length of children list - no of branches 
		self.__branches = 0
		# Task mode - idle, leaf, branch
		self.__type = 'branch'
		# Branch/Leaf Worker list for this task 
		self.__wid = []
		# Sap worker list for this node
		self.__sapwid = []
		# Task level - idle,progress,pending,approved,sap,complete
		self.status = 'idle' 
		#Msg structure
		self.__msg = tms.new_msg('idle',None,tid,None);
		
	@property 
	def id(self):
		return self.__tid;

	@property 
	def children(self):
		return self.__children

	@property 
	def wid(self):
		return self.__wid.pop()

	@property 
	def type(self):
		return self.__type;

	@property
	def parent(self):
		if self.__parent is not None:
			return self.__parent

        def finished_supervision(self):
                for c in self.__children:
                        if(c.status == 'pending' or c.status == 'progress'):
                                return False
                return True
        
        def sapify_leaf(self):
                self.status='complete'
                self.__msg['sap_data'] = self.__msg['leaf_data']
                self.__msg['sap_task'] = self.__msg['leaf_task']
                
        def collect_sap(self):
                for c in self.__children :
                        if(c.status != complete):
                                return False                        
                for c in self.__children :
                        self.__msg['sap_task'].append(c.sap_task)
                        self.__msg['sap_work'].append(c.sap_data)     
                        

                return True
        
	def msg(self):
		return self.__msg

	def add_child(self,id):
		self.__children.append(id)
		self.__branches += 1

	def del_child(self,id):
		self.__children.remove(id)
		self.__branches -= 1;

	def copy_msg(self,msg):
		self.__type = msg['mode']			# Update node's current type - leaf/branch/sap stage 
		# if leaf,update msg with leaf-results and change mode to pending
		if(msg['mode'] == 'leaf'):			# Handle leaf node
			if msg['WID'] not in self.__wid:	# Add leaf worker to wid list 
				self.__wid.append(msg['WID'])
			self.__msg['leaf_data']	= msg['leaf_data']
			self.__msg['leaf_task']	= msg['leaf_task']
			self.__status			= 'pending'
		print 'copy_msg: msg is ' + str(msg)

		if(msg['mode'] == 'branch'):		# Add branch worker to wid list 
			if msg['WID'] not in self.__wid:
				self.__wid.append(msg['WID'])
			self.__msg['branch_data']		= copy.copy(msg['branch_data'])
			self.__msg['branch_task']		= copy.copy(msg['branch_task'])
			self.__msg['branch_data_type']	= copy.copy(msg['branch_data_type'])
			self.__status					= 'pending'
			#print 'Branch msg is ' + str(msg)

		if(msg['mode'] == 'sap'):			# Add sap worker to wid list 
			self.__sapwid.append(msg['WID'])# RJ: in sap mode, does wid mean sap_wid?
                        self.__msg['sap_data'] = msg['sap_data']
                        self.__msg['sap_rating'] = msg['sap_rating']
                        self.__msg['sap_reject'] = msg['sap_reject']

		if(msg['mode'] == 'super'):
                        self.__msg['super_feedback'] = msg['super_feedback']
                        self.__msg['super_approve'] = msg['super_approve']
                        
		return 

	def fill_newmsg(self,msg,index=0):
		# Update new tasks's msg structure					
		newmsg 				= self.__msg
		newmsg['mode']		= msg['branch_data_type'][index]
		if (newmsg['mode'] 	 == 'leaf'):
			newmsg['leaf_task']		= msg['branch_data'][index]
		elif (newmsg['mode'] == 'branch'):
			newmsg['branch_task']	= msg['branch_data'][index]
		#print "New msg is " + str(self.__msg)
		return

	def notify_super(self,taskid):
		self.__msg['super_task_id'] = taskid
                #####add some fields for super stuff
		self.__msg['mode'] = 'super'
		self.__msg['super_mode'] = 'approved'
		self.__msg['WID'] = self.__wid()
		tm.send_task(self.__msg)

	# Notify the worker that they must wait for approval 
	def notify_worker(self,workid,super_mode='unapproved',notify=1):
                self.__msg['mode']              = 'super'
		self.__msg['super_mode']	= super_mode
		self.__msg['WID'] 			= workid
		if(notify == 1):
			tm.send_task(self.__msg)	
		return

	def requestmsg(self,req_task=None):
		if req_task is None:
			self.__msg['branch_task'] 	= 'Hi there, can you help me plan a 5 day trip to NYC ? Some details for planning \
			1. A cruise ride\
			2. Shopping\
			3. Broadway show\
			4. 3 star Hotels\
			5. Delta Airlines'
		else:
			self.__msg['branch_task'] = req_task

		self.__msg['mode']			= 'branch'
		self.__msg['preference']	= 'branch'
		return 


		


