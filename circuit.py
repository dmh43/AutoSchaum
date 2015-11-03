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
import sympy


class Node:
    """
    contains information about which devices are connected to which nodes and which nodes are supernodes and gnd
    :type num_comp_connected: int
    :type y_connected: int
    :type connected_comps: list[components.Component]
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
        self.connected_comps = []  # connected components
        self.voltage = float('NaN')
        self.node_num = self._num_nodes.next()
        self.branchlist = []
        """:type : list[Branch]"""

    def add_comp(self, comp):
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
        self.connected_comps.append(comp)
        if isinstance(comp, components.Impedance):
            self.y_connected += comp.y
        return self

# TODO maybe add_comp should be done when the component is instantiated?

# TODO generate equations for node voltage analysis
# TODO solve equations with sympy
# TODO dependent voltage sources
# TODO reorganize in a way that makes the next step easy
# TODO shrink fuctions
# TODO each circuit should have it's own components etc
# TODO draw circuits

class Supernode:
    """
        This class contains information about a group of nodes which form a supernode. Nodes that make up a supernode
        are interfaced only through the supernode class instance. The voltage and node number of the supernode are
        identical to those of the master node.
    """

    def __init__(self, branches):
        """
            :type branches: list[Branch]
            :return:
        """
        # self.nodedict = {connected_nodes[i].node_num : connected_nodes[i] for i in range(len(connected_nodes))}  # list of nodes that are a part of the supernode
        self.nodelist = [node for node in list(itertools.chain(*[branch.nodelist for branch in branches]))]
        """:type : list[Node]"""
        # TODO I dont think these next two values will be used
        self.num_comp_connected = sum([i.num_comp_connected for i in self.nodelist])
        """:type : int"""
        self.y_connected = sum([i.y_connected for i in self.nodelist])
        """:type : int"""
        self.master_node = self.nodelist[0]  # the master node is the first node that inserted into the supernode
        """:type : Node"""
        self.branchlist = []
        """:type : list[Branch]"""
        for branch in branches:
            branch.supernode = self
            self.add_branch(branch)

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

    def add_branch(self, branch):
        self.branchlist.append(branch)
        #for comp in branch.component_list:
            #self.add_comp(comp)
        self.nodelist.extend(branch.nodelist)
        self.nodelist = list(set(self.nodelist))


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
        """:type : list[Node]"""
        self.component_list = []
        """:type : list[components.Component]"""
        self.branch_num = self._num_branches.next()
        self.supernode = None
        """:type : Supernode"""

    def add_node(self, node):
        """
        :type node: Node
        :param node:
        :return:
        """
        self.nodelist.append(node)
        node.branchlist.append(self)

    def ending_nodes(self):
        return [self.nodelist[0], self.nodelist[-1]]


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
        """:type : file"""
        self.netlist = self.netlist_file.read().split('\n')
        """:type : str"""
        self.name = self.netlist[0]
        """:type : str"""
        self.netlist = self.netlist[1:]
        """:type : str"""
        self.nodedict = {}
        """:type : dict[int, Node]"""
        self.nontrivial_nodedict = {}
        """:type : dict[int, Node]"""
        self.reduced_nodedict = {}
        """:type : dict[int, Node]"""
        self.component_list = []
        """:type : [components.Component]"""
        self.supernode_list = []
        """:type : list[Supernode]"""
        self.branchlist = []
        """:type : list[Branch]"""
        self.ym = [[]]
        """:type : list[list[int]]"""
        self.num_nodes = 0
        """:type : int"""
        self.equations = []
        """:type : list[str]"""
        self.ref = None
        """:type : Node"""
        self.numerators = []
        self.denomenators = []

    def create_nodes(self):
        """
        parses self.netlist to create nodes
        :return:
        """
        self.num_nodes = max([max(int(comp.split(' ')[1]), int(comp.split(' ')[2])) for comp in self.netlist]) + 1
        # this compensates for zero indexing
        for i in range(self.num_nodes):
            self.nodedict[i] = Node()

    def create_supernodes(self):
        """
        Creates supernodes for the given circuit
        :return:
        """
        # create list of all branches which contain voltage sources
        v_source_branches = [comp.branch for comp in self.component_list if isinstance(comp, components.VoltageSource)]
        """:type : list[Branch]"""
        # create list of all branches which contain only voltage sources
        v_source_branches = [branch for branch in v_source_branches if all([isinstance(
            branch.component_list[i], components.VoltageSource) for i in range(len(branch.component_list))])]
        if len(v_source_branches) == 1:
            self.supernode_list.append(Supernode([v_source_branches[0]]))
            return
        for branch in v_source_branches:
            for comparison in list(set(v_source_branches) - set(branch)):
                assert isinstance(comparison, Branch)
                for node in branch.ending_nodes():
                    if node in comparison.ending_nodes():
                        if branch.supernode is None and comparison.supernode is None:
                            self.supernode_list.append(Supernode([branch]))
                            self.supernode_list.append(Supernode([comparison]))
                        elif branch.supernode is not None:
                            branch.supernode.add_branch(comparison)
                        elif comparison.supernode is not None:
                            comparison.supernode.add_branch(branch)

    def sub_super_nodes(self):
        internal_nodes = []
        for sn in self.supernode_list:
            internal_nodes.extend(list(set(sn.nodelist)-set([sn.master_node])))
        for node in self.nodedict:
            if self.nodedict[node] not in internal_nodes:
                self.reduced_nodedict[node] = self.nodedict[node]

    def define_reference_voltage(self):
        """
        The user should be allowed to select the reference node!
        This function defines the reference voltage to be the node with the most components connected
        :return:
        """
        self.ref = sorted(self.reduced_nodedict.values(), key = lambda node: node.num_comp_connected)[-1]

    def populate_nodes(self):
        for comp in self.netlist:
            data = comp.split(' ')
            """:type : list[str]"""
            new_comp = components.create_component(data[0], self.component_list, data[3],
                                                   (self.nodedict[int(data[1])],
                                                    self.nodedict[int(data[2])]))
            """:type : components.Component"""
            new_comp.pos.add_comp(new_comp)
            new_comp.neg.add_comp(new_comp)

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
        for comp in node1.connected_comps:
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
        for node in self.nodedict.values():
            if node.num_comp_connected > 2:
                self.nontrivial_nodedict[node.node_num] = node

    def create_branches(self):
        # This can be recursive!
        if len(self.nontrivial_nodedict.values()) == 0:
            current_branch = Branch()
            current_branch.component_list = self.component_list
            for node in self.nodedict.values():
                current_branch.add_node(node)
            map(lambda comp: setattr(comp, 'branch', current_branch), self.component_list)
            self.branchlist.append(current_branch)
            return
        for node in self.nontrivial_nodedict.values():
            for direction in list(set([x.pos if (x.neg == node) else x.neg for x in node.connected_comps])):
                assert isinstance(direction, Node)
                if direction.num_comp_connected > 2:
                    # This only happens when two nodes are connected by a single component. therefore each component
                    # is a part of its own branch.
                    for comp in self.connecting(node, direction):
                        current_branch = Branch()
                        current_branch.add_node(node)
                        current_branch.add_node(direction)
                        current_branch.component_list.append(comp)
                        comp.branch = current_branch
                        if current_branch.nodelist[0] in [x.nodelist[-1] for x in self.branchlist] or \
                                        current_branch.nodelist[-1] in [x.nodelist[0] for x in self.branchlist]:
                            break
                        else:
                            self.branchlist.append(current_branch)
                    continue  # this direction has been exhausted, so go to the next direction
                current_branch = Branch()
                current_branch.add_node(node)  # The start node
                current_branch.add_node(direction)  # The direction to go down
                current_branch.component_list.extend(self.connecting(node, direction))
                map(lambda comp: setattr(comp, 'branch', current_branch), self.connecting(node, direction))
                while True:  # Go down each one until you reach the end of the branch. I think this will find all branches
                    if current_branch.nodelist[-1].num_comp_connected > 2:
                        # reached end of branch
                        self.branchlist.append(current_branch)
                        break
                    next_comp = set(current_branch.nodelist[-1].connected_comps) - set(current_branch.component_list)
                    next_comp = next_comp.pop()
                    """:type : components.Component"""
                    next_node = next_comp.pos if next_comp.neg == current_branch.nodelist[-1] else next_comp.neg
                    """:type : Node"""
                    if next_node in current_branch.nodelist:
                        # looped around a branch somehow... look into this...
                        self.branchlist.append(current_branch)
                        break
                    current_branch.add_node(next_node)
                    # jump to the other node of the component connected to this node and add it to the list
                    current_branch.component_list.extend(
                        self.connecting(current_branch.nodelist[-2], current_branch.nodelist[-1]))
                    # add the component connecting the new node and the last node
                    map(lambda comp: setattr(comp, 'branch', current_branch),
                        self.connecting(current_branch.nodelist[-2], current_branch.nodelist[-1]))
                    if current_branch.nodelist[0] in [x.nodelist[-1] for x in self.branchlist] or \
                                    current_branch.nodelist[-1] in [x.nodelist[0] for x in self.branchlist]:
                        break  # if the branch has already been added, but in reverse then break
                        # and dont add a new branch to the branchlist
                        # This will work because it checks to see if the array is flipped. ie it only checks for
                        # finding the same branch but in the opposite direction
                    else:
                        self.branchlist.append(current_branch)
                        break

    # TODO need a method to identify other node of a component when looking from the first node
    # TODO need a method to identify directionality of voltage sources easily
    # TODO modify code to encorporate those changes
    # TODO identify items in parallel with each other
    # TODO evaluate currents through easy to calculate branches

    def identify_voltages(self):
        return
        # TODO recursively define this
        self.ref.voltage = 0
        #while
        for comp in self.ref.connected_comps:
            if isinstance(comp, components.VoltageSource):
                other_node(comp, self.ref).voltage = comp.v
        for comp in filter(lambda elem: isinstance(elem, components.VoltageSource), self.component_list):
            for next_comp in (filter(lambda elem: isinstance(elem, components.VoltageSource), comp.pos.connected_comps) + filter(lambda elem: isinstance(elem, components.VoltageSource), comp.neg.connected_comps)):
                other_node(next_comp, other_node(comp, self.ref)).voltage = other_node(comp, self.ref)

    def gen_node_voltage_eq(self):
        """
        :rtype: list[str]
        :return: list of strings to be sympified into sympy expressions
        """
        # TODO finish this!
        for node in list(set(self.reduced_nodedict.values()) - set([self.ref])):
            for branch in node.branchlist:
                self.numerators.append([node])
                self.denomenators.append([0])
                for comp in branch.component_list:
                    if isinstance(comp, components.VoltageSource):
                        self.numerators[-1].extend(["-", comp])
                    elif isinstance(comp, components.Resistor):
                        self.denomenators[-1].append([comp])
                    if comp.pos != node and comp.pos in self.reduced_nodedict.values():  # reached end of branch?
                        self.numerators[-1].extend(["-", comp.pos])
                    if comp.neg != node and comp.neg in self.reduced_nodedict.values():
                        self.numerators[-1].extend(["-", comp.neg])

    def calc_admittance_matrix(self):
        self.ym = [[complex(0, 0) for i in range(self.num_nodes)] for j in range(self.num_nodes)]
        for node1 in self.nodedict.values():
            for node2 in self.nodedict.values():
                if node1 == node2:
                    for comp in node1.connected_comps:
                        if isinstance(comp, components.Impedance):
                            self.ym[node1.node_num][node1.node_num] += comp.y
                        else:
                            continue
                else:
                    for comp in self.connecting(node1, node2):
                        if isinstance(comp, components.Impedance):
                            self.ym[node1.node_num][node2.node_num] -= comp.y


class Cursor:
    """
    In order to traverse a circuit it becomes easier and more intuitive to imagine a cursor moving along branches and
    loops and between nodes. It will make it easier to solve circuits using node voltage and mesh analysis. It will
    also simplify the use of KVL and KCL.
    """
    def __init__(self):
        self.current_node = None
        """:type: Node"""
        self.previous_nodes = []
        """:type: list[Node]"""
        self.previous_branches = []
        """:type: list[Branch]"""

    def step(self):
        """takes a step down the branch that it is currently on"""

    def directions(self):
        """
        Returns a dictionary of lists containing the directions the cursor can go separated into two lists
        :rtype: dict[str, list[Node]]
        """

    def current_branch(self):

def other_node(comp, node):
    """
    :type comp: components.Component
    :type node: Node
    :return:
    """
    if comp.pos == Node:
        return comp.neg
    else:
        return comp.pos
