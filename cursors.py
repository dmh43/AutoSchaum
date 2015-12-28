import helper_funcs
import components

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
        connecting_list = helper_funcs.connecting(node, self.location)
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
        unseen_connecting_list = self.unseen(helper_funcs.connecting(node, self.location))
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
        return self.step_to(helper_funcs.other_node(self.unseen_vsources_connected()[0], self.location))

    def step_back(self):
        self.step_to(self.breadcrumbs.pop())

    def directions(self):
        """
        Returns a list containing the directions (nodes) the cursor can go
        :rtype: list[Node]
        """
        return [helper_funcs.other_node(comp, self.location) for comp in self.location.connected_comps]

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
                new_direcs.append(helper_funcs.other_node(comp, self.location))
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
        destination = helper_funcs.other_node(component_to_jump_over, self.location)
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
        for comp in helper_funcs.connecting(self.location, node):
            self.branch.add_comp(comp)
        super(BranchCreatorCursor, self).step_to(node)
        self.branch.add_node(node)
        return helper_funcs.connecting(self.last_node_seen(), node)

    def step_along(self, node):
        new_comp_seen = super(BranchCreatorCursor, self).step_along(node)
        self.branch.add_comp(new_comp_seen)
        self.branch.add_node(node)
        return new_comp_seen

    def step_along_branch(self):
        return super(BranchCreatorCursor, self).step_along_branch()
