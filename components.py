__author__ = 'Dany'
import math
import circuit


class Component:
    """
    :type nodes: list[circuit.Node]
    :type name: str
    """
    def __init__(self, nodes, name):
        self.nodes = nodes
        self.refdes = name
        self.branch = None

    @property
    def neg(self):
        """
        :rtype: circuit.Node
        :return:
        """
        return self.nodes[1]

    @property
    def pos(self):
        """
        :rtype: circuit.Node
        :return:
        """
        return self.nodes[0]

class Impedance(Component):
    def __init__(self, real, reactive, nodes, name):
        """
        nodes should be in the form (pos_node, neg_node)
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
    return comp_list[-1]