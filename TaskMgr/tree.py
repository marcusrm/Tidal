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
                self.__sq   	 = pq()					# sapper Priority Queue
		self.__qlen	 = 0					# Queue length
		self.__sqlen	 = 0					# sapper Queue length
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

	############################# sapper Priority Queue Methods##############################
	def get_sq_len(self):					# Get the current length of the queue
		return self.__sqlen					

	@property 
	def get_sq(self):						# Get a copy of the queue
		print self.__sq

	def add_to_sq(self,priority,tid):
		self.__sq.put_nowait((priority,tid)) # Put task in queue
		self.__sqlen += 1					# Keep queue length count
		print 'TidalQueue: Add element - len is ' +str(self.__sqlen)

	def get_sq_elem(self):
		elem = self.__sq.get_nowait();		# Pull next task from queue
		self.__sqlen -= 1					# Decrement queue length
		print "TidalQueue: Removed element - len is" + str(self.__sqlen)
		return elem 						# Return TID of next task in queue

	############################# Task Tree Methods ##################################### 
	@property 
	def nodes(self):						# Returns dict of all nodes in the tree
		return self.__nodes

	def get_task_count(self):				# Returns dict of active task counts
		return self.__atasks

        def get_parent(self,child):
                return self[child.parent]

        def is_root(self,tid):
                return (tid == self.__root)
        
	def set_requestTask(self,task_str=None, amt=40):
		if self.__root != 0 :
			print 'TaskMgr:Main task is already set ! Go back and sleep'
			return False
		else :
			tid 						= hashlib.sha512(str(self.__count)+'haw').hexdigest()
                        self.__count+=1
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

	def add_node(self,tid,parent=None,type='branch') :
		#print 'Create Node: ' + str(tid)
		if parent is not None:
			node = Node(tid,parent,type)				# Create a task node
                     #   import pdb; pdb.set_trace()
			self[tid] = node 					# Add node to the class Dict
			self[parent].add_child(tid)			# Add to parent's child
			print self[parent].children
			self.add_to_q(self.__count,tid)		# Add task to the priority queue based on creation order
			return node
		else:
			if ts.LOCAL_TESTING == True:
                                pass
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

		#self.display(self,self.__root);

        def finished_supervision(self,tid):
                for c in self[tid].children:
                        if(self[c].status == 'pending' or self[c].status == 'progress' or self[c].status == 'idle'):
                                return False
                if(not self[tid].children):
                        return False
                return True
                
        def generate_branches(self,omsg,tid):
                #msg = self[tid].msg()
                #add nodes to the tree
                #print msg
                branch_count = len(omsg['branch_data'])
                print 'Tree.py: '+ str(branch_count)+' new Branch nodes added '
                for i in range(0,branch_count):
                        msg = tms.new_msg()
                        msg['mode'] = omsg['branch_data_type'][i]
                        if(msg['mode'] == 'branch'):
                                msg['branch_task'] = omsg['branch_data'][i]
                        elif(msg['mode'] == 'leaf'):
                                msg['leaf_task'] = omsg['branch_data'][i]
                                
                        # Add new node to the tree
                        newtid = hashlib.sha512(str(self.__count)+'haw').hexdigest()	
                        msg['TID'] = newtid
                        self.__count 	+= 1				
                        newnode 		 = self.add_node(newtid,tid,msg['mode'])
                        
                        self.__atasks[omsg['branch_data_type'][i]] += 1
                        #newnode.fill_newmsg(msg,i);
                        newnode.fill_msg(msg);
                        
        def generate_sap(self,tid):
                self.add_to_sq(0,tid)
                
	def ask_approval(self,msg):
		# Send message to supervisor to approve the task
                child = self[msg['TID']]
                child.status = 'pending'
                print "ASK APPROVAL"
                if(self.is_root(child.id) is False):
                        self[child.parent].notify_super(msg)
                        child.notify_worker(msg['WID'],'unapproved') 

        def collect_sap(self,parent):
                for c in parent.children :
                        if(self[c].status != "complete"):
                                return False
                for c in parent.children :
                        parent.get_child_sap(self[c])
                        
                return True
                        
        def update_sap(self,child):
                if(self.is_root(child.id)):
                        #notify requester
                        print"UPDATE SAP ON ROOT, notify req?"
                        return
                if(self.collect_sap(self[child.parent])):
                        self[child.parent].status = 'sap'
                        self.generate_sap(self[child.parent].id)
                
        def process_sap(self,msg):
                child = self[msg['TID']]
                is_rejected = False
                for i in range(0,len(msg['sap_reject'])):
                        if(msg['sap_reject'][i] is True):
                                redo = self[msg['sap_task_ids'][i]]
                                redo.status = 'idle'
                                self.add_to_q(0,redo.id)
                                is_rejected=True
                                
                if(is_rejected is False):                
                        self.save_results(msg)
                        self.update_sap(child)
                
                        if(self.is_root(child.id) is False):
                                parent = self[child.parent]
                                if(self.finished_supervision(parent.id)):
                                        parent.state = 'sap' 
                                        wm.W.complete(parent.wid,False)
                                        msg['mode']='idle'
                                        msg['WID']=parent.wid
                                        parent.send(msg)
                        else:
                             print "NOTIFY REQUESTER, task is done.  "       


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
                return self[tid].type
        
	def __getitem__(self,key):
		return self.__nodes[key]

	def __setitem__(self,key,item):
		self.__nodes[key] = item

	def __delitem__(self,key):
		del self.__nodes[key]


TaskTree    = Tree()
