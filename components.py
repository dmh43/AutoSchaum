__author__ = 'Dany'
import math

component_types = ('R', 'C', 'L', 'Z', 'V', 'I', 'VCVS', 'CCVS', 'VCIS', 'VVIS')

class Impedance:
    def __init__(self, real, reactive, nodes):
        """
        nodes should be in the form (pos_node, neg_node)
        """
        self.z = complex(real, reactive)
        self.y = 1/self.z
        self.nodes = nodes


class Voltage_Source:
    def __init__(self, real, reactive, nodes):
        self.v = complex(real, reactive)
        self.nodes = nodes
