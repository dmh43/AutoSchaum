__author__ = 'Dany'
import math
import circuit
from helper_funcs import *

class Component(object):
    """
    :type nodes: list[circuit.Node]
    :type name: str
    :type branch: circuit.Branch
    """
    def __init__(self, nodes, name):
        self.nodes = nodes
        self.refdes = name
        self.branch = None
        self.node_current_in = None
        """:type : circuit.Node"""
        # node_current_in gives node where current enters (passive sign convention)

    @property
    def neg(self):
        """
        :rtype: circuit.Node
        :return:
        """
        return self.nodes[0]

    @property
    def pos(self):
        """
        :rtype: circuit.Node
        :return:
        """
        return self.nodes[1]

    @property
    def voltage(self):
        """
        Voltage drop across the component from pos to neg
        :return:
        """
        return self.pos.voltage - self.neg.voltage

    @property
    def current(self):
        """
        Returns the current entering the pos node of the component
        This is consistent with passive sign convention
        :return:
        """
        # TODO this method makes it apparent that a Current class would be helpful since you want direction and magnitude
        if self.has_branch():
            if self.branch.current_is_defined():
                if self.pos == self.node_current_in:  #if the positive node is where current enters (passive sign convention)
                    return self.branch.current
                elif self.neg == self.node_current_in:
                    return -self.branch.current  # flip if self.pos is away from the current entry of the branch
        else:
            return

    # @property
    # def power(self):
    #     """
    #     Passive sign convention defined power
    #     :return:
    #     """
    #     return self.current*self.voltage

    def parallel(self):
        """
        :rtype : list[Component]
        """
        parallel_comps = []
        for comp in self.pos.connected_comps:
            if other_node(comp, self.pos) == self.neg:
                parallel_comps.append(comp)
        for comp in self.neg.connected_comps:
            if other_node(comp, self.neg) == self.pos:
                parallel_comps.append(comp)
        return parallel_comps

    def has_branch(self):
        if self.branch:
            return True
        else:
            return False

    def high_node(self, ref_node):
        """
        given a component, returns the node (pos or neg) closest to ref node in a branch
        This tells you the directionality of the comp in the branch
        """
        node1 = self.pos
        node2 = self.neg
        if node1 == ref_node:
            return node1
        elif node2 == ref_node:
            return node2
        first_cursor = circuit.Cursor(node1)
        second_cursor = circuit.Cursor(node2)
        while (first_cursor.location != ref_node and
               second_cursor.location != ref_node):
            first_cursor.step_forward_away(node2)
            second_cursor.step_forward_away(node1)
        if first_cursor.location == ref_node:
            return node1
        else:
            return node2

class Impedance(Component):
    def __init__(self, real, reactive, nodes, name):
        """
        nodes should be in the form (neg_node, pos_node)
        """
        self.z = complex(real, reactive)
        self.y = 1/self.z
        self.nodes = nodes
        self.refdes = name
        self.branch = None


class Resistor(Impedance):
    def __init__(self, real, nodes, name):
        self.z = complex(real,0)
        self.y = 1/self.z
        self.nodes = nodes
        self.refdes = name
        self.branch = None


class Capacitor(Impedance):
    def __init__(self, reactive, nodes, name):
        self.z = complex(0, reactive)
        self.y = 1/self.z
        self.nodes = nodes
        self.refdes = name
        self.branch = None


class Inductor(Impedance):
    def __init__(self, reactive, nodes, name):
        self.z = complex(0, reactive)
        self.y = 1/self.z
        self.nodes = nodes
        self.refdes = name
        self.branch = None


class CurrentSource(Component):
    pass


class VCVS(Component):
    pass


class CCVS(Component):
    pass


class VCIS(Component):
    pass


class ICIS(Component):
    pass


class VoltageSource(Component):
    def __init__(self, real, reactive, nodes, name):
        self.v = complex(real, reactive)
        self.nodes = nodes
        self.refdes = name
        self.branch = None

    def set_other_node_voltage(self):
        """
        when the voltage is defined at one node of a voltage source, the other end is easy to define.
        This function sets the voltage at the node that does not have a value if exactly one node has a defined voltag.
        otherwise the function does nothing
        """
        # TODO some error handling can go in here
        if self.pos.voltage_is_defined():
            self.neg.voltage = self.pos.voltage - complex(self.v, 0)  # TODO will need to fix this for compelx voltages
        elif self.neg.voltage_is_defined():
            self.pos.voltage = self.neg.voltage + complex(self.v, 0)  # TODO will need to fix this for compelx voltages


component_types = {'R':Resistor, 'C':Capacitor, 'L':Inductor, 'Z':Impedance, 'V':VoltageSource, 'I':CurrentSource,
    'VCVS':VCVS, 'CCVS':CCVS, 'VCIS':VCIS, 'ICIS':ICIS}


def create_component(name, comp_list, value, nodes):
    """
    :rtype: Component
    :type name: string
    :param name: the name of the component from the netlist
    :param value: the value of (or expression for) the component being created
    :type comp_list: list[Component]
    :param comp_list: the dictionary that keeps track of the list of components
    :type nodes: type([circuit.Node])
    :param nodes: the list of nodes that the device connects to (pos, neg)
    :return: returns a refrence to the component that has been created
    """
    if name[0] == 'R':
        comp_list.append(Resistor(float(value), nodes, name))
    elif name[0] == 'C':
        pass
    elif name[0] == 'L':
        pass
    elif name[0] == 'Z':
        comp_list.append(Impedance(complex(value).real, complex(value).imag, nodes, name))
    elif name[0] == 'V':
        comp_list.append(VoltageSource(complex(value).real, complex(value).imag, nodes, name))
    elif name[0] == 'I':
        pass
    elif name[0:4] == "VCVS":
        pass
    elif name[0:4] == "VCIS":
        pass
    elif name[0:4] == "CCVS":
        pass
    elif name[0:4] == "ICIS":
        pass
    for node in nodes:
        node.add_comp(comp_list[-1])
    return comp_list[-1]