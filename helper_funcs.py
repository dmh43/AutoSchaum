__author__ = 'Dany'

from circuit import *
import components

def only_vsources(comp_list):
    """
    Filters a list of components and returns the sublist of voltage sources
    :type comp_list: list[components.Component]
    :return:
    :rtype: list[components.VoltageSource]
    """
    return filter(lambda comp: isinstance(comp, components.VoltageSource), comp_list)


def only_resistances(comp_list):
    """
    Filters a list of components and returns the sublist of resistances
    :type comp_list: list[components.Component]
    :return:
    :rtype: list[components.Resistor]
    """
    return filter(lambda comp: isinstance(comp, components.Resistor), comp_list)


def other_node(comp, node):
    """
    :type comp: components.Component
    :type node: Node
    :return:
    """
    if comp.pos == node:
        return comp.neg
    else:
        return comp.pos


def only_branchless(comps):
    """
    filters out all components that have been assigned branches
    :type comps: list[components.Component]
    :return:
    """
    return filter(lambda comp: not comp.has_branch(), comps)


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

def high_node(self, comp, ref_node):
    """
    given a component, returns the node (pos or neg) closest to ref node in a branch
    This tells you the directionality of the comp in the branch
    """
    node1 = comp.pos
    node2 = comp.neg
    if node1 == ref_node:
        return node1
    elif node2 == ref_node:
        return node2
    first_cursor = Cursor(node1)
    second_cursor = Cursor(node2)
    while (first_cursor.location != ref_node and
           second_cursor.location != ref_node):
        first_cursor.step_forward_away(node2)
        second_cursor.step_forward_away(node1)
    if first_cursor.location == ref_node:
        return node1
    else:
        return node2