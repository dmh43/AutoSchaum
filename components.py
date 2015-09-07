__author__ = 'Dany'
import math


class Component:
    def __init__(self, nodes):
        self.nodes = nodes

    @property
    def neg(self):
        """
        :return: Node
        """
        return self.nodes[1]

    @property
    def pos(self):
        """
        :return: Node
        """
        return self.nodes[0]

class Impedance(Component):
    def __init__(self, real, reactive, nodes):
        """
        nodes should be in the form (pos_node, neg_node)
        """
        self.z = complex(real, reactive)
        self.y = 1/self.z
        self.nodes = nodes


class Resistor(Impedance):
    def __init__(self, real, nodes):
        self.z = complex(real,0)
        self.y = 1/self.z
        self.nodes = nodes


class Capacitor(Impedance):
    def __init__(self, reactive, nodes):
        self.z = complex(0, reactive)
        self.y = 1/self.z
        self.nodes = nodes


class Inductor(Impedance):
    def __init__(self, reactive, nodes):
        self.z = complex(0, reactive)
        self.y = 1/self.z
        self.nodes = nodes


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
    def __init__(self, real, reactive, nodes):
        self.v = complex(real, reactive)
        self.nodes = nodes


component_types = {'R':Resistor, 'C':Capacitor, 'L':Inductor, 'Z':Impedance, 'V':VoltageSource, 'I':CurrentSource,
    'VCVS':VCVS, 'CCVS':CCVS, 'VCIS':VCIS, 'ICIS':ICIS}

def create_component(name, comp_list, value, nodes):
    """
    :type name: string
    :param name: the name of the component from the netlist
    :param value: the value of (or expression for) the component being created
    :type comp_list: dict
    :param comp_list: the dictionary that keeps track of the list of components
    :type nodes: type([Node])
    :param nodes: the list of nodes that the device connects to (pos, neg)
    :return: returns a refrence to the component that has been created
    """
    if name[0] == 'R':
        comp_list[name] = Resistor(float(value), nodes)
    elif name[0] == 'C':
        pass
    elif name[0] == 'L':
        pass
    elif name[0] == 'Z':
        comp_list[name] = Impedance(complex(value).real, complex(value).imag, nodes)
    elif name[0] == 'V':
        comp_list[name] = VoltageSource(complex(value).real, complex(value).imag, nodes)
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
    return comp_list[name]