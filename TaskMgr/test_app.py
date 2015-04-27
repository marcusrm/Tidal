from tree import Tree
import myconst

tree = Tree()

tree.add_node("Task")
tree.add_node("B1","Task")
tree.add_node("B2","Task")
tree.add_node("B3","Task")
tree.add_node("B4","B1")
tree.add_node("B5","B2")
tree.add_node("L1","B5")
tree.add_node("B6","B2")
tree.add_node("L2","B6")

tree.display("Task")
'''
tree.remove_node("B5",myconst.YES)
tree.add_node("B5","B2")
tree.add_node("L1","B5")
tree.display("Task")
tree.remove_node("B5",myconst.NO)
tree.display("Task")
tree.display_dict()

print("***** DEPTH-FIRST ITERATION *****")
for node in tree.traverse("Task"):
    print(node)
print("***** BREADTH-FIRST ITERATION *****")
for node in tree.traverse("Task", mode=BREADTH):
    print(node)
'''