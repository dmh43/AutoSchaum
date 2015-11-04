__author__ = 'Dany'

from circuit import *

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


def connecting(node1, node2):
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
