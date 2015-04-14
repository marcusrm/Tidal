from node import Node
import taskconst


''' Tree dictionary looks like this 
{ node_id : node_obj of class Node,
  next_id : next node_obj .... }
'''
class Tree:

	def __init__(self):
		self.__nodes = {} #Dict of nodes

	@property 
	def nodes(self):
		return self.__nodes
	# Add node to the tree dictionary, add id to teh parent's child-list
	def add_node(self,id,parent=None):
		''' Create  a new node '''
		node = Node(id,parent)
		self[id] = node # Add to the class Dict

		if parent is not None:
			self[parent].add_child(id)

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
		children = self[id].children
		#print self[id].parent
		
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
	def activeTaskNum():pass

	def supervisionTaskNum():pass


	def __getitem__(self,key):
		return self.__nodes[key]

	def __setitem__(self,key,item):
		self.__nodes[key] = item

	def __delitem__(self,key):
		del self.__nodes[key]
