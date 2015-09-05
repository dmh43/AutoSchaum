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
# TODO do some concept validation before testing
# TODO ok... do some testing before proceeding
import components
import process_director


class Node:
    """
    contains information about which devices are connected to which nodes and which nodes are supernodes and gnd
    """

    def __init__(self):
        """
        self.voltage_list is defined as a list of other node voltages which are summed into sum_voltage
        :return:
        """
        self.num_connected = 0  # number of devices connected to this node
        self.y_connected = 0  # sum of admittances connected
        self.voltage_list = [float('NaN')] # not a number until expression of voltages is defined
        self.voltage = float('NaN')
        self.supernode = False

    def include_in_supernode(self, super_node):
        """
        :type super_node: Supernode
        :param super_node:
        :return:
        """
        self.supernode = super_node
        return

    def add_comp(self, parent_circuit, comp, to_nodes):
        """
        add a component that is connected to this node
        :type parent_circuit: Circuit
        :param comp: can be a source or an impedance
        :param to_nodes: list of other nodes that the component is connected to
        :return:
        """
        self.num_connected += 1
        self.connected.append(comp)
        if type(comp) == components.Impedance:
            self.y_connected += comp.y
        if type(comp) == components.Voltage_Source:
            parent_circuit.supernode_list.append(self)
            # how should i define the voltages between nodes?? self.


class Supernode(Node):
    """This class contains information about a group of nodes which form a supernode."""


    def __init__(self, connected_nodes):
        """

        :type connected_nodes: type([Node])
        :return:
        """
        self.nodes = connected_nodes # list of nodes that are a part of the supernode
        self.num_connected = sum([i.num_connected for i in self.nodes])
        self.y_connected = sum([i.y_connected for i in self.nodes])
        self.voltage_list
        # TODO ok... i need to figure out how im going to calculate the result. Do i need voltage_list in both nodes and super nodes?


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
        self.nodelist = []
        self.supernode_list = []
        self.ym = [[]]

    def create_nodes(self):
        """
        parses self.netlist to create nodes
        :return:
        """
        for comp in self.netlist:
            if self.num_nodes < max(comp.split(' ')[1], comp.split(' ')[2]):
                self.num_nodes = max(comp.split(' ')[1], comp.split(' ')[2]) #this can be done with list comprehension
        director = process_director.ProcessDirector()
        for comp in range(self.num_nodes):
            self.nodelist.append(director.construct(comp, Node))
# TODO: Make sure this function works. Should be adding nodes dynamically

    def add_node(self, node_to_add):
        self.nodelist.append(node_to_add)

    def populate_nodes(self):
        for node in self.nodelist:
            for comp in self.netlist:
                data = comp.split(' ')
                node.add_comp(self, data[0], (data[1], data[2]), data[3])
                #is this correct???

    def __calc_admittance_matrix(self):
        self.num_components = len(self.netlist)
        for node in self.nodelist:
            for component in node.connected:
                if type(component) == components.Impedance:
                    self.ym[component.nodes[0]][component.nodes[1]] += component.y
                    self.ym[component.nodes[1]][component.nodes[0]] += component.y

                    #TODO maybe i just need t create some unit tests...
