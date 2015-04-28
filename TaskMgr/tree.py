from node import Node
import tidal_msg as tms
import taskconst
import copy
import hashlib
from Queue import PriorityQueue as pq

global TaskQueue


''' Task Priprity Queue Structure '''
class TidalQueue:
	def __init__(self):
		self.__q   = pq()
		self.__len	   = 0

	@property 
	def get_q_len(self):					# Get the current length of the queue
		return self.__len					

	@property 
	def get_q(self):						# Get a copy of the queue
		return self.__q

	def add_to_q(self,priority,tid):
		self.__q.put_nowait((priority,tid)) # Put task in queue
		self.__len += 1					    # Keep queue length count

	def get_q_elem(self):
		elem = self.__q.get_nowait();		# Pull next task from queue
		self.__len -= 1						# Decrement queue length
		return elem[1]						# Return TID of next task in queue


''' Task Tree Structure '''
class Tree:
	def __init__(self):
		self.__nodes = {} #Dict of nodes
		self.__root  = 0
		self.__count = 1

	@property 
	def nodes(self):
		return self.__nodes

	# Add node to the tree dictionary, add id to the parent's child-list
	def add_node(self,tid,parent=None):
		''' Create  a new node '''

		node = Node(tid,parent)
		self[id] = node 						# Add to the class Dict
		if parent is not None:
			self[parent].add_child(tid)
			print self[parent].children
		else:									#Store tree root id to access the dictionary 'nodes'
			self.__root = tid
			node.requestmsg()

		TaskQueue.add_to_q(self.__count,tid)#add task to the priority queue based on creation time
		return node

	def remove_node(self,id,subtree=taskconst.YES):
		''' Delete a node form the dict of Tree class.
		Note that all its children will be deleted as well'''
		#Delete from Parent's child list
		parent = self[id].parent
		print "Node "+id + "'s subtree deleted -",
		if subtree is taskconst.YES:
			self.del_node(id)
	 	self[parent].del_child(id)
		# Delete from Tree Dict
		del self[id]

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
			print "**************Branch node "
			branch_count = len(msg['branch_data'])
			for i in range(0,branch_count):
				# Add new node to the tree
				newtid = hashlib.sha512(str(self.__count)+'haw').hexdigest()	
				self.__count += 1				
				newnode = self.add_node(newtid,tid)
				newnode.fill_newmsg(msg,i);
		else:
			print "**************Leaf node type = " + msg['mode']

		#self.display(self,self.__root);


	def ask_approval(self,tid):
		# Send message to supervisor to approve the task
		if(self[tid].status == 'pending'):
			self[tid].parent.notify_super(tid)

	def wait_for_approval(self,tid,wid): 							# Send a socket message to the worker 
		self[tid].notify_worker(wid)									# to wait for work-approval
		return

	def get_task(self,type):							# Look for tasks of mode 'type'
		queue = self.__nodes[self.__root]
		while queue:
			yield queue[0]
			next = self[queue[0]].children				# 'next' is a list of children 
			if self[next].type == type:					# if type is a match, return this node's structure
				print 'Found a free task of type \
				'+type+':TaskId is '+next   
				break; 
                #return 1;#next.msg
			else:
				queue = queue[1:] + next


	def supervisionTaskNum():pass

	def get_maintask(self):									# Return TID of the root task
		if(self.__root is not 0):
			return self.__root
		else:
			print 'Root not set yet !!!Check for the control flow'
			return self.__root
	def getmsgcp(self,tid):
		msg = tms.new_msg()
		msg = copy.deepcopy(self[tid].msg())
		return msg

	def __getitem__(self,key):
		return self.__nodes[key]

	def __setitem__(self,key,item):
		self.__nodes[key] = item

	def __delitem__(self,key):
		del self.__nodes[key]

# Define a structure of class type TidalQueue
TaskQueue = TidalQueue()
