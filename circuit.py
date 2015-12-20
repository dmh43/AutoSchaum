__author__ = 'Dany'
""" Each circuit is read from a netlist where each line has the following format:
        [component refdes] [list of nodes to connect to] [value]
        and the first line is the name of the circuit
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
    The design philosphy is pretty undefined at this point so I encourage others to make changes
        in accordance to their own preferences. However, I am a fan of DRY and KISS and try to implmenet
        those here wherever I can and wherever I remember to.
"""
import components
from helper_funcs import *
from cursors import *

import math
import cmath
import itertools
import sympy
import copy


class Node(object):
    """
    Represents a node in the circuit and holds the data relevant to it. Here, a node is defined as the junction
    connecting two components
    :type num_comp_connected: int
    :type y_connected: int
    :type connected_comps: list[components.Component]
    :type voltage: float
    :type node_num: int
    """

    def __init__(self, node_num):
        """
        instantiates a node object. An empty node is created and then components are connected using class methods
        :return: Init functions do not return a value
        """
        self.y_connected = 0  # sum of admittances connected
        """:type : int"""
        self.connected_comps = []  # connected components
        """:type : list[components.Component]"""
        self.voltage = float('NaN')
        """:type : complex"""
        self.node_num = node_num
        """:type : int"""
        self.branchlist = []
        """:type : list[Branch]"""

    @property
    def num_comp_connected(self):
        """
        :return: Number of components connected to this node
        """
        return len(self.connected_comps)

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
        self.connected_comps.append(comp)
        if isinstance(comp, components.Impedance):
            self.y_connected += comp.y
        return self

    def voltage_is_defined(self):
        # TODO check that Voltage class is compatible with this. otherwise consider modifying it.
        if self.voltage == 0:
            return True
        elif isinstance(self.voltage, float) and math.isnan(self.voltage):
            return False
        elif isinstance(self.voltage, complex) and cmath.isnan(self.voltage):
            return False
        elif self.voltage:
            return True
        else:
            return False

    def kcl_is_easy(self):
        """
        Determines whether KCL is easy to evaluate at this node.
        # TODO should be overloaded later to include options for all KCL options
        """
        return len(self.undefined_current_branches()) == 1

    def undefined_current_branches(self):
        return filter(lambda branch: not branch.current_is_defined(), self.branchlist)

    def numeric_kcl(self): # TODO Is there a better way to do this other than making the node state dependent?
        """
        performs kcl at a node if all the connected branches except one have defined current values and sets
        the current at the unknown branch. Otherwise raise an exception
        :return:
        """
        if not self.kcl_is_easy():
            raise Exception('KCL is not easy at node {0}'.format(self.node_num))
        current_leaving_node = []
        unknown_branch_current = self.undefined_current_branches()[0]
        known_current_branches = list(set(self.branchlist) - set([unknown_branch_current]))
        for branch in known_current_branches:
            if branch.node_current_in == self:
                current_leaving_node.append(branch.current)
            else:
                current_leaving_node.append(-branch.current)
        unknown_branch_current.current = sum(current_leaving_node)
        return current_leaving_node

    def node_voltage_kcl(self):
        """
        Creates the KCL equations for node analysis and sets the current expression, current exps string and sympy eqs
        for that branch
        :return: Returns a list containing the expressions for the currents leaving the node
        :rtype: list[CurrentExp]
        """
        current_leaving_node = []
        for branch in self.branchlist:
            branch_impedances = []
            branch_voltages = [Voltage(self)]
            kcl_cursor = KCLCursor(branch, self)
            if branch.node_current_in == self: flip_direction = False  # in same direction as branch current?
            else: flip_direction = True
            if branch.current_is_defined():
                if flip_direction:
                    current_leaving_node.append(-1*branch.current)
                else:
                    current_leaving_node.append(branch.current)
                continue
            elif branch.current_exp_is_defined():
                new_current_exp = copy.deepcopy(branch.current_expression)
                if flip_direction:
                    new_current_exp.flip_dir()
                current_leaving_node.append(new_current_exp)
                continue
            while True:
                new_comp = kcl_cursor.step_down_branch()[0]  #assuming only one component
                if isinstance(new_comp, components.Resistor):
                    branch_impedances.append(new_comp)
                if isinstance(new_comp, components.VoltageSource):
                    directionality = 1
                    if new_comp.neg != kcl_cursor.location:
                        directionality = -1  # the factor to multiply by the source voltage to compensate for directionality
                    branch_voltages.append(Voltage(new_comp, directionality))
                if kcl_cursor.at_branch_end:
                    branch_voltages.append(Voltage(kcl_cursor.location))  # we interperate this as a voltage to gnd
                    break
            current_leaving_node.append(CurrentExp(branch_voltages, branch_impedances))
            branchs_perspective_voltage = copy.deepcopy(branch_voltages)
            branch.current_expression = CurrentExp(branchs_perspective_voltage, branch_impedances)
            if flip_direction:
                branch.current_expression.flip_dir()
            branch.current = branch.current_expression.into_sympy()
        return current_leaving_node

# TODO write a function for flipping the current direction using the node_current_in

# TODO test component currents and other tests

# TODO dependent voltage sources
# TODO draw circuits

class Supernode(object):
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
        self.master_node = self.nodelist[0]  # the master node is the first node that inserted into the supernode
        """:type : Node"""
        self.branchlist = []
        """:type : list[Branch]"""
        for branch in branches:
            branch.supernode = self
            self.add_branch(branch)

    @property
    def voltage_is_defined(self):
        return self.master_node.voltage_is_defined()

    @property
    def voltage(self):
        return self.master_node.voltage

    @property
    def node_num(self):
        return self.master_node.node_num

    @property
    def num_comp_connected(self):
        return self.master_node.num_comp_connected

    def evaluate_voltages(self):
        """
        This function will evaluate and assign voltage values to each node inside a supernode.
        """
        if math.isnan(self.voltage):  # this function should only run after the matrix equation has been
            # solved
            return False
        else:
            # TODO finish
            cursor = Cursor(self.master_node)

    def add_branch(self, branch):
        self.branchlist.append(branch)
        self.nodelist.extend(branch.nodelist)
        self.nodelist = list(set(self.nodelist))


class Branch(object):
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

    def __init__(self, branch_number):
        self.nodelist = []
        """:type : list[Node]"""
        self.component_list = []
        """:type : list[components.Component]"""
        self.branch_num = branch_number
        """:type : int"""
        self.supernode = None
        """:type : Supernode"""
        self.current = None
        """:type : complex"""
        self.current_expression = None
        """Ultimately, this value should be summed for impedance and va - v1 -v2... for voltages and then take z/v"""

    def __eq__(self, other_branch):
        """
        :type other_branch: Branch
        :return:
        """
        return (self.component_list == other_branch.component_list or
                self.component_list[::-1] == other_branch.component_list)

    def __ne__(self, other_branch):
        return not (self == other_branch)

    def __hash__(self):
        return hash(self.branch_num)

    @property
    def node_current_in(self):
        if self.nodelist:
            return self.nodelist[-1]

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

    def is_complete_branch(self):
        # TODO add capability to detect a branch that is the whole circuit
        return self.nodelist[-1].num_comp_connected > 2

    def current_is_defined(self):
        if self.current == 0:
            return True
        elif isinstance(self.current, float) and math.isnan(self.current):
            return False
        elif isinstance(self.current, complex) and cmath.isnan(self.current):
            return False
        elif self.current:
            return True
        else:
            return False

    def current_exp_is_defined(self):
        if self.current_expression is None:
            return False
        else:
            return True

    def add_comp(self, comp):
        """
        :type comp: components.Component
        :return:
        """
        if comp.has_branch():  # TODO change this and modify create_branches to exit branch creation
            return
        if comp in self.component_list:
            return
        self.component_list.append(comp)
        comp.branch = self
        comp.node_current_in = comp.high_node(self.node_current_in)
        return comp


class Circuit(object):
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
        A Circuit contains all the information which is relevant to the representation of a circuit
        """
        self.netlist_file = None
        """:type : file"""
        self.netlist = None
        """:type : str"""
        self.name = None
        """:type : str"""
        self.netlist = None
        """:type : str"""
        self.nodedict = {}
        """:type : dict[int, Node]"""
        self.nontrivial_nodedict = {}
        """:type : dict[int, Node]"""
        self.reduced_nodedict = {}
        """:type : dict[int, Node]"""
        self.non_trivial_reduced_nodedict = {}
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
        self.ref = None
        """:type : Node"""

    def load_netlist(self, netlist_file):
        self.netlist = netlist_file.read().split('\n')
        self.name = self.netlist[0]
        self.netlist = self.netlist[1:]

    @property
    def num_branches(self):
        return len(self.branchlist)

    def create_nodes(self):
        """
        parses self.netlist to create nodes
        :return:
        """
        self.num_nodes = max([max(int(comp.split(' ')[1]), int(comp.split(' ')[2])) for comp in self.netlist]) + 1
        # this compensates for zero indexing
        for i in range(self.num_nodes):
            self.nodedict[i] = Node(i)

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
            for comparison in list(set(v_source_branches) - set([branch])):
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
        This function deines the reference voltage to be the node with the most components connected
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

    def identify_nontrivial_nodes(self):
        """
        This function identifies the nontrivial nodes of a circuit. Specifically, this means all nodes that are
        connected to more than two components.
        :return:
        """
        for node in self.nodedict.values():
            if node.num_comp_connected > 2:
                self.nontrivial_nodedict[node.node_num] = node

    def identify_nontrivial_nonsuper_nodes(self):
        for node in self.reduced_nodedict.values():
            if node.num_comp_connected > 2:
                self.non_trivial_reduced_nodedict[node.node_num] = node

    def create_branches(self):
        if len(self.nontrivial_nodedict.values()) == 0:
            current_branch = Branch(self.num_branches+1)
            for node in self.nodedict.values():
                current_branch.add_node(node)
            for comp in self.component_list:
                current_branch.add_comp(comp)
        for node in self.nontrivial_nodedict.values():
            if not only_branchless(node.connected_comps):  # if all conncomps have branches
                # TODO maybe wrap in a function^
                continue
            new_branch = Branch(self.num_branches+1)
            new_branch.add_node(node)
            branch_cursor = BranchCreatorCursor(node, new_branch)
            while only_branchless(node.connected_comps):  # no more branchless conncomps
                while True:
                    branch_cursor.step_along_branch()
                    if new_branch.is_complete_branch():
                        break
                if new_branch not in self.branchlist:
                    if new_branch.component_list:  #if not empty
                        self.branchlist.append(new_branch)
                    else:
                        for undo_node in new_branch.nodelist:
                            undo_node.branchlist.pop()  # TODO oh... this is ugly. fix it. plz
                else:
                    for undo_node in new_branch.nodelist:
                        undo_node.branchlist.pop()  # TODO oh... this is ugly. fix it. plz
                if not only_branchless(node.connected_comps):  # if all conncomps have branches
                    # TODO maybe wrap in a function^
                    break
                new_branch = Branch(self.num_branches+1)
                new_branch.add_node(node)
                branch_cursor.branch = new_branch  # TODO wrap in method?
                branch_cursor.location = node

# TODO more general equality method for branches and fix ramifications


    def printer(self):
        for node in self.nodedict.values():
            print("Node {0} is at {1} V".format(node.node_num, node.voltage))
        for comp in self.component_list:
            print("Current through {0} is {1} A".format(comp.refdes, comp.current))

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
                    for comp in connecting(node1, node2):
                        if isinstance(comp, components.Impedance):
                            self.ym[node1.node_num][node2.node_num] -= comp.y






class Direction(object):
    """I dont know if this will actually be useful"""
    pass


class Voltage(Direction):
    def __init__(self, v_source_or_node, dir_encountered=1):
        self.voltage = v_source_or_node
        self.direction = dir_encountered

    def into_sympy(self):
        pass

# TODO maybe a Current class should be created which is just a value or current expression and node
class CurrentExp(Direction):
    def __init__(self, voltage_list, impedances):
        """
        :param voltages: Voltages in the form: Start Node, Vsource encountered..., End Node
        :param impedances:
        :return:
        """
        self.voltages = voltage_list
        """:type : list[Voltage]"""
        self.impedances = impedances
        """:type : list[components.Impedance]"""
        self.denominator = ""
        """:type : str"""
        self.numerator = ""
        """:type : str"""
        self.str_expr = None
        """:type : str"""
        self.sympy_expr = None

    def flip_dir(self):
        for emf in self.voltages:
            emf.direction *= -1

    def into_str(self):
        numerator = "(V{0}".format(self.voltages[0].voltage.node_num)
        for emf in self.voltages[1:-1]:
            if emf.direction == -1:
                numerator += "- "
            numerator += "-" + emf.voltage.refdes
        numerator += "- V{0})/".format(self.voltages[-1].voltage.node_num)
        denom = "("
        for impedance in self.impedances:
            denom += "+" + impedance.refdes
        denom += ")"
        self.numerator = numerator
        self.denominator = denom
        self.str_expr = numerator+denom
        return self.str_expr

    def into_sympy(self):
        self.sympy_expr = sympy.sympify(self.str_expr)

