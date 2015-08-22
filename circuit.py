__author__ = 'Dany'
""" Each circuit is represented by a netlist where each line has the following format:
        [component refdes] [list of nodes to connect to] [value]
    Component Types:
        -Resistor 'R'
        -Capacitor 'C'
        -Inductor 'L'
        -Complex Impedance 'Z'
        -Voltage source 'V'
        -Current source 'I'
        -Voltage Controlled voltage source 'VCVS'
        -Current controlled voltage source 'CCVS'
        -Voltage controlled current source 'VCIS'
        -Current controlled current source 'CCIS'
    Default units are:
        -Impedance: Ohms
        -Voltage source: V
        -Current Source: A
    Each circuit has a corresponding admittance matrix and current injection vector:
        I = YV; where I and V are vectors and Y is a matrix
"""

from components import *
import impedance

class Node:
    """
    contains information about which devices are connected to which nodes and which nodes are supernodes and gnd
    """

    def __init__(self):
        """
        :return:
        """
        self.name = node_num
        self.num_connected = 0  # number of devices connected to this node
        self.y_connected = 0  # sum of admittances connected

    def add_comp(self, comp, to_nodes):
        """
        add a component that is connected to this node
        :param comp: can be a source or an impedance
        :param to_nodes: list of other nodes that the component is connected to
        :return:
        """
        self.num_connected += 1
        if type(comp) == impedance.Impedance:
            self.y_connected += comp.y


class Circuit:


    def __init__(self, netlist_filename):
        """
        the input circuit is in the form of a SPICE netlist
        This implies that each impedance (admittance) is specified by a impedance and two nodes that connect it
        Additionally, each voltage or current source is defined by a constant or an expression of other values
        A typical netlist looks like:
        CIRCUIT NAME
        V1 0 1 5
        R1 0 1 1
        R2 0 2 10
        R3 1 2 1
        """
        self.netlist_file = open('netlist_filename', 'r')
        self.netlist = self.netlist_file.read().split('\n')
        self.name = self.netlist[0]
        self.netlist = self.netlist[1:]

    def create_nodes(self):
        """
        parses self.netlist to create nodes
        :return:
        """
        for comp in self.netlist:
            comp.split(' ')


    def add_node(self, node_to_add):
        self.nodelist.append(node_to_add)

    def __calc_admittance_matrix(self):
        self.num_components = len(self.netlist)
        for component in self.netlist:
