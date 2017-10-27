from algorithm import Reasoner
from visualise import Visualiser

r = Reasoner()
v = Visualiser()

# Run reasoner with trace
root = r.create_graph(verbose=True)

# Visualise graph
v.process(root)
v.show()
