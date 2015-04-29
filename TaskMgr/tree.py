from node import Node
import tidal_msg as tms
import tidal_settings as ts
import taskconst
import copy
import hashlib
from Queue import PriorityQueue as pq


''' Task Tree Structure '''
class Tree():
	def __init__(self):
		self.__nodes = {} 					# Dict of nodes
		self.__root  = 0					# Root TID - Requester's task
		self.__count = 0					# tid count generator
		self.__q   	 = pq()					# Priority Queue
		self.__qlen	 = 0					# Queue length
		self.__atasks= {}				 	# Active leaf tasks
		self.__amt	 = 0					# Total cash allocated for the task

	############################# Priority Queue Methods##############################
	def get_q_len(self):					# Get the current length of the queue
		return self.__qlen					

	@property 
	def get_q(self):						# Get a copy of the queue
		print self.__q

	def add_to_q(self,priority,tid):
		self.__q.put_nowait((priority,tid)) # Put task in queue
		self.__qlen += 1					# Keep queue length count
		print 'TidalQueue: Add element - len is ' +str(self.__qlen)

	def get_q_elem(self):
		elem = self.__q.get_nowait();		# Pull next task from queue
		self.__qlen -= 1					# Decrement queue length
		print "TidalQueue: Removed element - len is" + str(self.__qlen)
		return elem 						# Return TID of next task in queue

	############################# Task Tree Methods ##################################### 
	@property 
	def nodes(self):						# Returns dict of all nodes in the tree
		return self.__nodes

	def get_task_count(self):				# Returns dict of active task counts
		return self.__atasks

	def set_requestTask(self,task_str=None, amt=40):
		if self.__root != 0 :
			print 'TaskMgr:Main task is already set ! Go back and sleep'
			return False
		else :
			tid 						= hashlib.sha512(str(self.__count)+'haw').hexdigest()
			node 						= Node(tid,None) # Create root node
			self[tid] 					= node 	# Add node to the class Dict
			self.__root 				= tid 	# Store root tid
			node.requestmsg(task_str)			# Fill msg details
			self.add_to_q(self.__count,tid) 	# Add task to the priority queue based on creation order
			self.__atasks['leaf']		= 0		# Set count of all active tasks
			self.__atasks['branch']		= 1		# Current root task is a branch
			self.__atasks['sap']		= 0
			self.__amt					= amt 	# Set amount allocated for the task
			return node

	def add_node(self,tid,parent=None) :
		#print 'Create Node: ' + str(tid) 
		if parent is not None:
			node = Node(tid,parent)				# Create a task node
			self[tid] = node 					# Add node to the class Dict
			self[parent].add_child(tid)			# Add to parent's child
			print self[parent].children
			self.add_to_q(self.__count,tid)		# Add task to the priority queue based on creation order
			return node
		else:
			if ts.LOCAL_TESTING == True:
				self.set_requestTask()
			# else:
				# print 'TaskMgr: Error! Task creation failed'

	def remove_node(self,id,subtree=taskconst.YES):
		parent = self[id].parent
		print "Del:Node "+id + "'s subtree"
		if subtree is taskconst.YES:			# Node's child-tree is deleted
			self.del_node(id)					
	 	self[parent].del_child(id)				# Delete node from all child lists
		del self[id]							# Delete a node form the dict of Tree class

	def del_node(self, id):
		'''Delete a node and all its subtree '''
		children = self[id].children
		if len(children) < 1:
			return 
		for child in children:
			self.del_node(child) # delete child lists
			#print child+",",
			del self.__nodes[child] # delete from tree

	def display(self,id,depth=taskconst.ROOT):
		''' Display the task tree '''
		if self[id] is not None:
			print self[id].children
		
		if depth == taskconst.ROOT:
			print "{0}".format(id)
		else:
			print '    '*depth,"{0}".format(id)

		depth += 1
		for child in children:
			self.display(child,depth) # recursive call
	
	def display_dict(self):
		''' Print the node dictionary'''
		print self.__nodes;
		#print self.__dict__;
	
	def traverse(self,id,mode=taskconst.DEPTH):
		''' DFS or BFS Traversal '''
		yield id
		queue = self[id].children
		while queue:
			yield queue[0]
			next = self[queue[0]].children
			if mode == DEPTH:
				queue = next + queue[1:]
			elif mode == BREATH:
				queue = queue[1:]+next
	
	def save_results(self,msg={}):
		tid = msg['TID']		
		self[tid].copy_msg(msg) 

		if(msg['mode'] == 'branch'):								#add nodes to the tree
			branch_count = len(msg['branch_data'])
			print 'Tree.py: '+ str(branch_count)+' new Branch nodes added '
			for i in range(0,branch_count):
				# Add new node to the tree
				newtid = hashlib.sha512(str(self.__count)+'haw').hexdigest()	
				self.__count 	+= 1				
				newnode 		 = self.add_node(newtid,tid)
				self.__atasks[msg['branch_data_type'][i]] += 1
				newnode.fill_newmsg(msg,i);
		#if (msg['mode'] == 'sap'):									# Add sapped data as input to parent node

		#self.display(self,self.__root);

	def ask_approval(self,tid):
		# Send message to supervisor to approve the task
		if(self[tid].status == 'pending'):
			self[tid].parent.notify_super(tid)

	def wait_for_approval(self,tid,wid): 							# Send a socket message to the worker 
		self[tid].notify_worker(wid,'unapproved')								# to wait for work-approval
		return

	def process_approval(self,wid,tid):								# Once approved by the parent/super, change state of the child
		if (self[tid].msg()['super_mode'] != 'unapproved'):		
			print 'TID '+tid +' is already approved or is idle'
			return 0	
		
		if(self[tid].type() == 'leaf'):
			self[tid].notify_worker(wid,'approved',notify=1)						# to approved state. TODO: Release worker
		#if (self[tid].type() == 'branch'):

	def get_task(self,type):										# Look for tasks of mode 'type'
		queue = self.__nodes[self.__root]
		while queue:
			yield queue[0]
			next = self[queue[0]].children							# 'next' is a list of children 
			if self[next].type == type:								# if type is a match, return this node's structure
				print 'Found a free task of type \
				'+type+':TaskId is '+next   
				break; 
                #return 1;#next.msg
			else:
				queue = queue[1:] + next


	def supervisionTaskNum():pass

	def get_maintask(self):											# Return TID of the root task
		if(self.__root is not 0):
			return self.__root
		else:
			print 'Root not set yet !!!Check for the control flow'
			return self.__root
	def getmsgcp(self,tid):
		msg =self[tid].msg()
		return msg

        def get_tid_type(self,tid):
                return self[tid].type()
        
	def __getitem__(self,key):
		return self.__nodes[key]

	def __setitem__(self,key,item):
		self.__nodes[key] = item

	def __delitem__(self,key):
		del self.__nodes[key]


TaskTree    = Tree()
