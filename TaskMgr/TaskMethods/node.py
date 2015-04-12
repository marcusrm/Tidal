# Define a node to represent a task here
class Node:
	def __init__(self,id,parent):
		#ID is a unique key used to store the nodes as a dictionary
		self.__id 		= id
		#List of dict keys for the dict stored in the tree class
		self.__children = [] 
		#Length of children list - no of branches 
		self.__branches = 0
		# Task state
		self.__status = 0
		# Parent of this node 
		self.__parent = parent
		# Worker list for creator, 
		self.__workers = {}
		#Task level 
		self.__level = 0
		
	@property 
	def id(self):
		return self.__id;

	@property 
	def children(self):
		return self.__children

	@property
	def parent(self):
		if self.__parent is not None:
			return self.__parent

	def add_child(self,id):
		self.__children.append(id)
		self.__branches += 1

	def del_child(self,id):
		self.__children.remove(id)
		self.__branches -= 1;


