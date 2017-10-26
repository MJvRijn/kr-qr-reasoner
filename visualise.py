import networkx as nx
import matplotlib.pyplot as plt


class Visualiser:
    G = nx.DiGraph()

    def process(self, node):
        self.G.add_node(str(node))

        for child in node.children:
            if str(child) not in self.G.nodes():
                self.process(child)

            self.G.add_edge(str(node), str(child))

    def show(self):
        nx.draw_circular(self.G, with_labels=True, arrows=True, node_size=0, node_color='c', node_shape='s', edge_color='r', font_size=6, width=1, alpha=0.8, linewidths=1)
        plt.show()
        pass

