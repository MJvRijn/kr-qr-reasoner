from algorithm_matt import Reasoner
from visualise import Visualiser

r = Reasoner()
v = Visualiser()

root = r.create_graph(verbose=True)

v.process(r.states[0])
v.show()
