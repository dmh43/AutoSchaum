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
from helper_funcs import *

import math
import cmath
import itertools
import sympy


class Node(object):
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

    def voltage_is_defined(self):
        # TODO this is a mess because of the way I am defining self.voltage. fix this plzzzz
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

    def solve_kcl(self):
        """
        Creates the KCL equations for the node. If it can be solved then it sets the current through that branch
        :return: Returns a list containing the expressions for the currents leaving the node
        :rtype: list[CurrentExp]
        """
        current_leaving_node = []
        if self.kcl_is_easy():
            unknown_branch_current = self.undefined_current_branches()[0]
            known_current_branches = list(set(self.branchlist) - set([unknown_branch_current]))
            for branch in known_current_branches:
                if branch.node_current_in == self:
                    current_leaving_node.append(branch.current)
                else:
                    current_leaving_node.append(-branch.current)
            unknown_branch_current.current = sum(current_leaving_node)
            return current_leaving_node
        else:
            for branch in self.branchlist:
                branch_impedances = []
                branch_voltages = [Voltage(self)]
                kcl_cursor = KCLCursor(branch, self)
                if branch.node_current_in == self: flip_direction = False  # in same direction as branch current?
                else: flip_direction = True
                while True:
                    new_comp = kcl_cursor.step_down_branch()[0]  #assuming only one component
                    if isinstance(new_comp, components.Resistor):
                        branch_impedances.append(new_comp)
                    if isinstance(new_comp, components.VoltageSource):
                        if new_comp.neg == kcl_cursor.location:
                            directionality = 1  # the factor to multiply by the source voltage to compensate for directionality
                        else:
                            directionality = -1
                        branch_voltages.append(Voltage(new_comp, directionality))
                    if kcl_cursor.at_branch_end:
                        branch_voltages.append(Voltage(kcl_cursor.location))  # we interperate this as a voltage to gnd
                        break
                current_leaving_node.append(CurrentExp(branch_voltages, branch_impedances))
                if flip_direction:
                    for voltage in branch_voltages[1:-1]:  # for all but the start and ending nodes
                        voltage.direction *= -1
                branch.current_expression = CurrentExp(branch_voltages, branch_impedances)
                branch.current = branch.current_expression.into_sympy()
            return current_leaving_node

# TODO write a function for flipping the current direction using the node_current_in

# TODO test component currents

# TODO write function to go back and forth until all easy ones are found, explaining along the way
# TODO equations for supernodes!!
# TODO solve equations with sympy
# TODO print equations and solutions

# TODO for jesus de christo adopt a consistent naming convention
# TODO dependent voltage sources
# TODO reorganize
# TODO add_comp should be done when the component is instantiated?
# TODO change the way we keep track of node num? Should be a global in the circuit
# TODO consider removing list comprehensions for something more easily debugggable
# TODO shrink fuctions
# TODO each circuit should have it's own components etc
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
    _num_branches = itertools.count(0)
    # TODO fix branch numbering

    def __init__(self):
        self.nodelist = []
        """:type : list[Node]"""
        self.component_list = []
        """:type : list[components.Component]"""
        self.branch_num = self._num_branches.next()
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
        self.equations = []
        """:type : list[str]"""
        self.ref = None
        """:type : Node"""
        self.numerators = []
        self.denomenators = []
        self.solved_is = False
        self.node_voltage_eqs_str = []
        """:type : list[str]"""
        self.node_voltage_eqs = []
        self.subbed_eqs = []
        self.solved_eq = None
        self.node_vars = []
        self.known_vars = []
        self.result = None

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
            new_comp.pos.add_comp(new_comp)
            new_comp.neg.add_comp(new_comp)

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
            current_branch = Branch()
            for node in self.nodedict.values():
                current_branch.add_node(node)
            for comp in self.component_list:
                current_branch.add_comp(comp)
        for node in self.nontrivial_nodedict.values():
            if not only_branchless(node.connected_comps):  # if all conncomps have branches
                # TODO maybe wrap in a function^
                continue
            new_branch = Branch()
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
                new_branch = Branch()
                new_branch.add_node(node)
                branch_cursor.branch = new_branch  # TODO wrap in method?
                branch_cursor.location = node

# TODO more general equality method for branches and fix ramifications

    def identify_voltages(self):
        self.ref.voltage = 0
        kvl_cursor = Cursor(self.ref)
        while True:
            while kvl_cursor.unseen_vsources_connected():  # While not empty
                first_unseen_source = only_vsources(kvl_cursor.step_down_unseen_vsource())[0] # will only contain a single vsource at most
                first_unseen_source.set_other_node_voltage()
            if kvl_cursor.location != self.ref:  # if you're no longer at ref
                kvl_cursor.step_back()
            elif not kvl_cursor.unseen_vsources_connected():  # if no more sources and at ref node
                break
            else:  # if at ref but more vsources to go then continue
                continue

    def identify_currents(self):
        """
        Defines the curent through the branch each resistor is in, in the direction going into the
        positive node of each resistor
        Also marks the node where the current enters the branch
        This is consistent with passive sign convention for that resistor
        :return:
        """
        for res in only_resistances(self.component_list):
            if res.node_current_in == res.pos:
                res.branch.current = res.voltage/res.z
            elif res.node_current_in == res.neg:
                res.branch.current = -res.voltage/res.z

    # TODO add another func for KCL but in terms of sympy equations where it can generate many sympy

    def gen_node_voltage_eq(self):
        """
        :rtype: list[str]
        :return: list of strings to be sympified into sympy expressions
        """
        for node in list(set(self.non_trivial_reduced_nodedict.values()) - set([self.ref])):
            current_exps = node.solve_kcl()
            for exp in current_exps:
                exp.into_str()
            self.node_voltage_eqs_str.append("+".join([exp.str_expr for exp in current_exps]))
            self.node_voltage_eqs.append(sympy.sympify(self.node_voltage_eqs_str[-1]))
            if not node.voltage_is_defined():
                self.node_vars.append(sympy.Symbol("V{0}".format(node.node_num)))
            else:
                self.known_vars.append((sympy.Symbol("V{0}".format(node.node_num), node.voltage)))

    # TODO circuit equations should be a class with progression

    def sub_into_eqs(self):
        for impedance in [imp for imp in self.component_list if isinstance(imp, components.Impedance)]:  # TODO move into another funfction
            self.known_vars.append(("{0}".format(impedance.refdes), impedance.z))
        self.known_vars.append(("V0", self.ref.voltage))  # TODO should be a class for this
        for eq in self.node_voltage_eqs:
            self.subbed_eqs.append(eq.subs(self.known_vars))

    #TODO group these two together to sub into an arbitrary expression after evaluating known vars

    def sub_into_result(self):
        self.result = self.solved_eq.subs(self.known_vars)

    def solve_eqs(self):
        self.solved_eq = sympy.solve(self.node_voltage_eqs, self.node_vars)

    def kcl_everywhere(self):
        for node in self.nontrivial_nodedict.values():
            node.solve_kcl()

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


class Cursor(object):
    """
    In order to traverse a circuit it becomes easier and more intuitive to imagine a cursor moving along branches and
    loops and between nodes. It will make it easier to solve circuits using node voltage and mesh analysis. It will
    also simplify the use of KVL and KCL.
    """
    def __init__(self, node):
        """
        :type node: Node
        :param node: The node to place the cursor at
        :return:
        """
        self.location = node
        """:type : Node"""
        self.nodes_seen = []
        """:type : list[Node]"""
        self.components_seen = []
        """:type : list[components.Component]"""
        self.breadcrumbs = []  # Keep track where you came from
        """:type : list[Node]"""

    def last_component_seen(self):
        return self.components_seen[-1]

    def last_node_seen(self):
        return self.nodes_seen[-1]

    def vsources_connected(self):
        return filter(lambda comp: isinstance(comp, components.VoltageSource), self.location.connected_comps)

    def unseen_vsources_connected(self):
        return filter(lambda vsource: vsource not in self.components_seen, self.vsources_connected())

    def step_to(self, node):
        """
        steps to a node connected to the current node and marks all the components connecting the two nodes as seen
        :param node:
        :type node: Node
        :return: the list of components stepped over (connecting to the current node and the next node)
        """
        connecting_list = connecting(node, self.location)
        if node not in self.directions():
            return self.location
        self.location = node
        self.components_seen.extend(connecting_list)
        self.nodes_seen.append(self.location)
        return connecting_list

    def unseen(self, comp_list):
        return filter(lambda comp: comp not in self.components_seen, comp_list)

    def step_along(self, node):
        """
        steps to a node connected to the current node and marks only
        the first unseen component as read (as if stepping along that component)
        :param node:
        :type node: Node
        :return: the component stepped along (the one marked as seen)
        """
        unseen_connecting_list = self.unseen(connecting(node, self.location))
        if node not in self.directions():
            raise ValueError
        self.location = node
        if not unseen_connecting_list:
            return []
        self.components_seen.append(unseen_connecting_list[0])
        self.nodes_seen.append(self.location)
        return unseen_connecting_list[0]

    def step_forward(self):
        """
        takes a step forward along the branch that it is currently on.  it returns the list of stepped over components
        When at the end of a branch (at a non-trivial node), the function returns without moving the cursor
        :return: the component that was stepped over
        """
        branch = self.current_branch()
        if isinstance(branch, list):
            return self.location
        self.breadcrumbs.append(self.location)
        # TODO breadcrumbs should be its own class but with  better name
        return self.step_to(self.new_directions()[0])

    def step_down_unseen_vsource(self):
        """
        Steps down the first unseen voltage source in the list
        :return: returns the list of components that was stepped over
        """
        self.breadcrumbs.append(self.location)
        return self.step_to(other_node(self.unseen_vsources_connected()[0], self.location))

    def step_back(self):
        self.step_to(self.breadcrumbs.pop())

    def directions(self):
        """
        Returns a list containing the directions (nodes) the cursor can go
        :rtype: list[Node]
        """
        return [other_node(comp, self.location) for comp in self.location.connected_comps]

    def new_directions(self):
        """
        Returns a list containing the directions (nodes) that the cursor can go but has not been to yet
        :rtype: list[Node]
        """
        new_direcs = []
        for comp in self.location.connected_comps:
            if comp in self.components_seen:
                continue
            else:
                new_direcs.append(other_node(comp, self.location))
        return new_direcs

    def new_alongs(self):
        unseen_alongs = []
        for comp in self.location.connected_comps:
            if comp in self.components_seen:
                continue
            else:
                unseen_alongs.append(comp)
        return unseen_alongs

    def current_branch(self):
        """
        returns the current branch that the cursor is traversing
        """
        if len(self.location.branchlist) == 1:
            return self.location.branchlist[0]
        return self.location.branchlist

    def step_along_branch(self):
        """
        This function will go down the first unseen branch
        :return: returns a list of the components connecting the old and new location
        :rtype: list[comp]
        """
        return self.step_along(self.new_directions()[0])

    @property
    def at_branch_end(self):
        if len(self.directions()) > 2:
            return True
        else:
            return False

    def step_forward_away(self, node):
        """
        Takes a step forward in the first direction away from node
        """
        # TODO change this and other similar functions to call a parent fun which has variable isntead of 0
        next_node_choices = [direc for direc in self.directions() if direc != node]
        return self.step_to(next_node_choices[0])


class KCLCursor(Cursor):
    """
    This class is used to easily step down branches when performing KCL at a node
    """
    def __init__(self, branch, start_node):
        """
        :type start_node: Node
        :type branch: Branch
        """
        super(KCLCursor, self).__init__(start_node)
        self.branch = branch

    def step_down_branch(self):
        for comp in self.branch.component_list:
            if ((self.location in comp.nodes) and (comp not in self.components_seen)):
                component_to_jump_over = comp
                break
        destination = other_node(component_to_jump_over, self.location)
        return self.step_to(destination)


class BranchCreatorCursor(Cursor):
    """
    This class takes a reference to a new branch and a node to start at
    and creates a cursor which adds components and nodes to the branch
    as it walks down it
    """
    def __init__(self, node, branch):
        """
        :type node: Node
        :type branch: Branch
        :return:
        """
        super(BranchCreatorCursor, self).__init__(node)
        self.branch = branch

    def step_to(self, node):
        for comp in connecting(self.location, node):
            self.branch.add_comp(comp)
        super(BranchCreatorCursor, self).step_to(node)
        self.branch.add_node(node)
        return connecting(self.last_node_seen(), node)

    def step_along(self, node):
        new_comp_seen = super(BranchCreatorCursor, self).step_along(node)
        self.branch.add_comp(new_comp_seen)
        self.branch.add_node(node)
        return new_comp_seen

    def step_along_branch(self):
        return super(BranchCreatorCursor, self).step_along_branch()


class Direction(object):
    """I dont know if this will actually be useful"""
    pass


class Voltage(Direction):
    def __init__(self, v_source_or_node, dir_encountered=1):
        self.voltage = v_source_or_node
        self.direction = dir_encountered

    def into_sympy(self):
        pass


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

    def into_str(self):
        numerator = "(V{0}".format(self.voltages[0].voltage.node_num)
        for emf in self.voltages[1:-1]:
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
