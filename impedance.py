__author__ = 'Dany'
import math


class Impedance:
    def __init__(self, real, reactive, nodes):
        """
        nodes should be in the form (pos_node, neg_node)
        """
        self.z = complex(real, reactive)
        self.y = 1/self.z
        self.nodes = nodes


