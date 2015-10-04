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

import math
import cmath
import itertools


class Node:
    """
    contains information about which devices are connected to which nodes and which nodes are supernodes and gnd
    :type num_comp_connected: int
    :type y_connected: int
    :type connected_comps: dict
    :type voltage: float
    :type node_num: int
    """
    _num_nodes = itertools.count(0)

    def __init__(self):
        """
        instantiates a node object. An empty node is created and then components are connected using class methods
        :return: Init functions do not return a value
        """
        self.num_comp_connected = 0  # number of devices connected to this node
        self.y_connected = 0  # sum of admittances connected
        self.connected_comps = {}  # connected components
        self.voltage = float('NaN')
        self.node_num = self._num_nodes.next()

    def add_comp(self, comp, name):
        """
        add a component that is connected to this node
        :type comp: components.Component
        :param comp: Component to add. Can be a source or an impedance
        :type name: string
        :param name: Name of the component to add
        :return: returns the node
        :rtype Node:
        """
        self.num_comp_connected += 1
        self.connected_comps[name] = comp
        if isinstance(comp, components.Impedance):
            self.y_connected += comp.y
        return self


# TODO generate equations for node voltage analysis
# TODO solve equations with sympy
# TODO each function should return a value and be well documeted
# TODO draw circuits
# TODO determine I vector

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
        if math.isnan(self.master_node.voltage):  # this function should only run after the matrix equation has been
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


class Branch:
    """
    Defines a branch connecting two nontrivial nodes
    self.nodelist gives the list of nodes in the order which they are encountered going from start (nodelist[0])
        to finish (nodelist[-1])
    self.component_list gives the list of components which are encountered when traversing the branch from start to
        finish. Either self.component_list[0].pos or self.component_list[0].neg is connected to nodelist[0] depending
        on the the orientation of the component in the cirucit.
    :type nodelist: list[Node]
    :type component_list: list[components.Component]
    :type branch_num: int
    """
    _num_branches = itertools.count(0)

    def __init__(self):
        self.nodelist = []
        self.component_list = []
        self.branch_num = self._num_branches.next()


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
        :type netlist_file: file
        :type netlist: str
        :type name: str
        :type nodelist: dict[str, Node]
        :type nontrivial_nodelist: dict[str, Node]
        :type component_list: dict[str, components.Component]
        :type supernode_list: dict[str, Supernode]
        :type branchlist: list[Branch]
        :type ym: list[list[int]]
        :type num_nodes: int
        
        """
        self.netlist_file = open(netlist_filename, 'r')
        self.netlist = self.netlist_file.read().split('\n')
        self.name = self.netlist[0]
        self.netlist = self.netlist[1:]
        self.nodelist = {}
        self.nontrivial_nodelist = {}
        self.component_list = {}
        self.supernode_list = {}
        self.branchlist = []
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

    def create_supernodes(self):
        """
        Creates supernodes for the given circuit
        :return:
        """
        return

    def define_reference_voltage(self):
        """
        The user should be allowed to select the reference node!
        :return:
        """
        pass

    def populate_nodes(self):
        for comp in self.netlist:
            data = comp.split(' ')
            """:type : list[str]"""
            new_comp = components.create_component(data[0], self.component_list, data[3],
                                                   (self.nodelist["Node %s" % (data[1])],
                                                    self.nodelist["Node %s" % (data[2])]))
            """:type : components.Component"""
            new_comp.pos.add_comp(new_comp, data[0])
            new_comp.neg.add_comp(new_comp, data[0])

    def connecting(self, node1, node2):
        """
        Gives all the components connected two nodes
        :param node1: The first node
        :type node1: Node
        :param node2: The node connected to the second node via a component
        :type node2: Node
        :return: A list containing all the components connecting node1 and node2
        :rtype list[components.Component:
        """
        comp_list = []
        """:type : list[components.Component]"""
        if node1 == node2:
            return []
        for comp in node1.connected_comps.values():
            if comp.neg == node2:
                comp_list.append(comp)
            elif comp.pos == node2:
                comp_list.append(comp)
        return comp_list

    def identify_nontrivial_nodes(self):
        """
        This function identifies the nontrivial nodes of a circuit. Specifically, this means all nodes that are
        connected to more than two components.
        :return:
        """
        for node in self.nodelist:
            if self.nodelist[node].num_comp_connected > 2:
                self.nontrivial_nodelist[node] = self.nodelist[node]

    def create_branches(self):
        if len(self.nontrivial_nodelist) == 0:
            self.branchlist.append(Branch())
            for node_num in range(self.num_nodes - 1, -1, -1):  # -1 and -1 are for bounds limiting for range()
                self.branchlist[0].component_list.append(self.nodelist["Node %d" % (node_num)])  # add sequentially
                return self.branchlist
        for node in self.nontrivial_nodelist.values():
            for direction in list(set([x.pos if (x.neg == node) else x.neg for x in node.connected_comps.values()])):
                if direction.num_comp_connected > 2:
                    # This only happens when two nodes are connected by a single component. therefore each component
                    # is a part of its own branch.
                    for comp in self.connecting(node, direction):
                        current_branch = Branch()
                        current_branch.nodelist.extend([node, direction])
                        current_branch.component_list.append(comp)
                        if current_branch.nodelist[0] in [x.nodelist[-1] for x in self.branchlist] or \
                                        current_branch.nodelist[-1] in [x.nodelist[0] for x in self.branchlist]:
                            break
                        else:
                            self.branchlist.append(current_branch)
                    continue  # this direction has been exhausted, so go to the next direction
                current_branch = Branch()
                current_branch.nodelist.append(node)  # The start node
                current_branch.nodelist.append(direction)  # The direction to go down
                current_branch.component_list.extend(self.connecting(node, direction))
                while True:  # Go down each one until you reach the end of the branch. I think this will find all branches
                    if current_branch.nodelist[-1].num_comp_connected > 2:
                        # reached end of branch
                        self.branchlist.append(current_branch)
                        break
                    next_comp = set(current_branch.nodelist[-1].connected_comps.values()) - set(current_branch.component_list)
                    next_comp = next_comp.pop()
                    """:type : components.Component"""
                    next_node = next_comp.pos if next_comp.neg == current_branch.nodelist[-1] else next_comp.neg
                    """:type : Node"""
                    if next_node in current_branch.nodelist:
                        # looped around a branch somehow... look into this...
                        self.branchlist.append(current_branch)
                        break
                    current_branch.nodelist.append(next_node)
                    # jump to the other node of the component connected to this node and add it to the list
                    current_branch.component_list.extend(
                        self.connecting(current_branch.nodelist[-2], current_branch.nodelist[-1]))
                    # add the component connecting the new node and the last node
                    if current_branch.nodelist[0] in [x.nodelist[-1] for x in self.branchlist] or \
                                    current_branch.nodelist[-1] in [x.nodelist[0] for x in self.branchlist]:
                        break  # if the branch has already been added, but in reverse then break
                        # and dont add a new branch to the branchlist
                        # This will work because it checks to see if the array is flipped. ie it only checks for
                        # finding the same branch but in the opposite direction
                    else:
                        self.branchlist.append(current_branch)
                        break

    def gen_node_voltage_eq(self):


    def calc_admittance_matrix(self):
        self.ym = [[complex(0, 0) for i in range(self.num_nodes)] for j in range(self.num_nodes)]
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
