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
import components
import process_director

import math
import cmath
import itertools


class Node:
    """
    contains information about which devices are connected to which nodes and which nodes are supernodes and gnd
    """
    _num_nodes = itertools.count(0)

    def __init__(self):
        """
        :return:
        """
        self.num_comp_connected = 0  # number of devices connected to this node
        self.y_connected = 0  # sum of admittances connected
        self.connected_comps = {}    # connected components
        self.voltage = float('NaN')
        self.node_num = self._num_nodes.next()

    def add_comp(self, comp, name):
        """
        add a component that is connected to this node
        :type comp: components.Component
        :param comp: Component to add. Can be a source or an impedance
        :type name: string
        :param name: Name of the component to add
        :return:
        """
        self.num_comp_connected += 1
        self.connected_comps[name] = comp
        if isinstance(comp, components.Impedance):
            self.y_connected += comp.y


class Supernode(Node):
    """
        This class contains information about a group of nodes which form a supernode. Nodes that make up a supernode
        are interfaced only through the supernode class instance
    """

    def __init__(self, connected_nodes):
        """
            :type connected_nodes: type([Node])
            :param connected_nodes: List of nodes that are a part of the supernode. The first node in the list is the master
            :return:
            """
        Node.__init__(self)
        self.nodes = connected_nodes  # list of nodes that are a part of the supernode
        self.num_comp_connected = sum([i.num_comp_connected for i in self.nodes])
        self.y_connected = sum([i.y_connected for i in self.nodes])
        self.master_node = self.nodes[0]  # the master node is the first node that inserted into the supernode

    def evaluate_voltages(self):
        """
        This function will evaluate and assign voltage values to each node inside a supernode. the return type is a
            success flag
        :return: type(True)
        """
        if math.isnan(self.master_node.voltage): # this function should only run after the matrix equation has been
                                                    # solved
            return False
        else:
            for comp in self.master_node.connected_comps:
                if type(comp) == components.VoltageSource:
                    if comp.pos == self.master_node:
                        comp.neg.voltage = self.master_node.voltage - comp.v
                    else:
                        comp.pos.voltage = self.master_node.voltage + comp.v
            return True


class Circuit:


    def __init__(self, netlist_filename):
        """
        the input circuit is in the form of a SPICE netlist
        This implies that each impedance (admittance) is specified by a impedance and two nodes that connect it
        Additionally, each voltage or current source is defined by a constant or an expression of other values
        :type netlist_filename: String
        :param netlist_filename: The filename of the netlist
        A typical netlist looks like:
        CIRCUIT NAME
        V1 0 1 5
        R1 0 1 1
        R2 0 2 10
        R3 1 2 1
        
        """
        self.netlist_file = open(netlist_filename, 'r')
        self.netlist = self.netlist_file.read().split('\n')
        self.name = self.netlist[0]
        self.netlist = self.netlist[1:]
        self.nodelist = {}
        self.component_list = {}
        self.supernode_list = {}
        self.ym = [[]]
        self.num_nodes = 0

    def create_nodes(self):
        """
        parses self.netlist to create nodes
        :return:
        """
        self.num_nodes = max([max(int(comp.split(' ')[1]), int(comp.split(' ')[2])) for comp in self.netlist]) + 1
            # this compensates for zero indexing
        for comp in range(self.num_nodes):
            self.nodelist["Node %d" % (comp)] = Node()
# TODO: Make sure this function works. Should be adding nodes dynamically

    def create_supernodes(self):
        """
        Creates supernodes for the given circuit
        :return:
        """
        return

    def populate_nodes(self):
        for node in self.nodelist.values():
            for comp in self.netlist:
                data = comp.split(' ')
                new_comp = components.create_component(data[0], self.component_list, data[3],
                                                       (self.nodelist["Node %s" % (data[1])],
                                                        self.nodelist["Node %s" % (data[2])]))
                node.add_comp(new_comp, data[0])
                # is this correct???

    def connecting(self, node1, node2):
        """
        Gives all the components connected two nodes
        :param node1: The first node
        :type node1: Node
        :param node2: The node connected to the second node via a component
        :type node2: Node
        :return: A list containing all the components connecting node1 and node2
        """
        comp_list = []
        if node1 == node2:
            return []
        for comp in node1.connected_comps.values():
            if comp.neg == node2:
                comp_list.append(comp)
            elif comp.pos == node2:
                comp_list.append(comp)
        return comp_list
    # TODO This is wrong

    def calc_admittance_matrix(self):
        self.ym = [[0]*self.num_nodes]*self.num_nodes
        for node1 in self.nodelist.values():
            for node2 in self.nodelist.values():
                if node1 == node2:
                    for comp in node1.connected_comps.values():
                        if isinstance(comp, components.Impedance):
                            self.ym[node1.node_num][node1.node_num] += comp.y
                        else:
                            continue
                else:
                    for comp in self.connecting(node1, node2):
                        if isinstance(comp, components.Impedance):
                            self.ym[node1.node_num][node2.node_num] -= comp.y
                            self.ym[node2.node_num][node1.node_num] -= comp.y

