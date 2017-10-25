import networkx as nx
import matplotlib.pyplot as plt


class Visualiser:
    G = nx.DiGraph()

    def process(self, node):
        self.G.add_node(str(node))

        print(len(node.children))
        for child in node.children:
            if str(child) not in self.G.nodes():
                self.process(child)

            self.G.add_edge(str(node), str(child))

    def show(self):
        nx.draw_spectral(self.G, with_labels=True, arrows=True, node_size=7500, node_color='c', node_shape='s', font_size=12, width=1, alpha=0.8, linewidths=1)
        plt.show()
        pass

