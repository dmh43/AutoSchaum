import cursors
import copy
import sympy
import helper_funcs
import components


class Solver(object):
    """
    Represents the Circuit solver. Keeps track of each step of the solution. Performs
    each solution step on each SolutionStep
    """
    def __init__(self, base_circuit):
        """
        :type base_circuit: Circuit
        """
        self.solution = [SolutionStep(base_circuit)]
        """:type : list[SolutionStep]"""

    def getcircuit(self):
        return self.solution[-1].circuit

    def setcircuit(self, circuit):
        self.solution[-1].circuit = circuit

    circuit = property(getcircuit, setcircuit)

    def identify_voltages(self):
        """performs KVL to identify and set voltages at nodes connected to ground through a component"""
        self.solution.append(copy.deepcopy(self.solution[-1]))
        self.solution[-1].ref.voltage = 0
        kvl_cursor = cursors.Cursor(self.solution[-1].ref)
        while True:
            while kvl_cursor.unseen_vsources_connected():  # While not empty
                first_unseen_source = helper_funcs.only_vsources(kvl_cursor.step_down_unseen_vsource())[0] # will only contain a single vsource at most
                first_unseen_source.set_other_node_voltage()
            if kvl_cursor.location != self.solution[-1].ref:  # if you're no longer at ref
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
        self.solution.append(copy.deepcopy(self.solution[-1]))
        for res in helper_funcs.only_resistances(self.solution[-1].circuit.component_list):
            if res.node_current_in == res.pos:
                res.branch.current = res.voltage/res.z
            elif res.node_current_in == res.neg:
                res.branch.current = -res.voltage/res.z

    # TODO add another func for KCL but in terms of sympy equations where it can generate many sympy. This is part of the larger idea of wrapping each operation in such a way that the program determines which operation to execute

    def gen_node_voltage_eq(self):
        """
        :rtype: list[str]
        :return: list of strings to be sympified into sympy expressions
        """
        self.solution.append(copy.deepcopy(self.solution[-1]))
        #for node in list(set(self.solution[-1].circuit.non_trivial_reduced_nodedict.values()) - {self.solution[-1].ref}):
        for node in [start_node for start_node in self.circuit.non_trivial_reduced_nodedict.values() if start_node.node_num != self.solution[-1].ref.node_num]:
            current_exps = node.node_voltage_kcl()
            for exp in current_exps:
                exp.into_str()
            self.solution[-1].node_voltage_eqs_str.append("+".join([exp.str_expr for exp in current_exps]))
            self.solution[-1].node_voltage_eqs.append(sympy.sympify(self.solution[-1].node_voltage_eqs_str[-1]))

    def determine_known_vars(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        for node in self.solution[-1].circuit.nodedict.values():
            if not node.voltage_is_defined():
                self.solution[-1].node_vars.append(sympy.Symbol("V{0}".format(node.node_num)))
            else:
                self.solution[-1].known_vars.append((sympy.Symbol("V{0}".format(node.node_num)), node.voltage))
        for comp in self.solution[-1].circuit.component_list:
            if isinstance(comp, components.Impedance):
                self.solution[-1].known_vars.append(("{0}".format(comp.refdes), comp.z))
            elif isinstance(comp, components.VoltageSource):
                self.solution[-1].known_vars.append(("{0}".format(comp.refdes), comp.v))

    def sub_zero_for_ref(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        # TODO make this such that the node num of ref actually chnges
        for eq in self.solution[-1].node_voltage_eqs:
            self.solution[-1].subbed_eqs.append(eq.subs("V{0}".format(self.solution[-1].ref.node_num), 0))

    def sub_into_eqs(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        for eq in self.solution[-1].node_voltage_eqs:
            self.solution[-1].subbed_eqs.append(eq.subs(self.solution[-1].known_vars))

    #TODO group these two together to sub into an arbitrary expression after evaluating known vars

    def sub_into_result(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        for eq in self.solution[-1].solved_eq.values():
            self.solution[-1].result.append(eq.subs(self.solution[-1].known_vars))

    def solve_eqs(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        self.solution[-1].solved_eq = sympy.solve(self.solution[-1].node_voltage_eqs, self.solution[-1].node_vars)

    def solve_subbed_eqs(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        self.solution[-1].solved_subbed_eq = sympy.solve(self.solution[-1].subbed_eqs, self.solution[-1].node_vars)
        # TODO fix this. sypy equations are mutable. An equation is not returned here, subbed_eqs is mutated

    def kcl_everywhere(self):
        self.solution.append(copy.deepcopy(self.solution[-1]))
        # TODO Honestly... what even is this?...
        for node in self.solution[-1].circuit.nontrivial_nodedict.values():
            node.solve_kcl() # TODO CHANGE THIS NAME

    def set_reference_voltage(self, node=0):
        """
        The user should be allowed to select the reference node!
        This function deines the reference voltage to be the node with the most components connected
        :type node: Node
        :return:
        """
        self.solution.append(copy.deepcopy(self.solution[-1]))
        if node == 0:
            self.solution[-1].ref = sorted(self.solution[-1].circuit.reduced_nodedict.values(), key = lambda node: node.num_comp_connected)[-1]
        else:
            self.solution[-1].ref = node #TODO fix this problem with copying circuits. Ref needs to be property. Other attributes tha tshould be properties to avoid this?? Or it can be a node number


class SolutionStep(object):
    """
    Contains a Circuit instance which represents a step in the solution
    """
    def __init__(self, circuit_to_solve):
        self.numerators = []
        self.denomenators = []
        self.equations = []
        """:type : list[str]"""
        self.solved_is = False
        self.node_voltage_eqs_str = []
        """:type : list[str]"""
        self.node_voltage_eqs = []
        self.subbed_eqs = []
        self.solved_subbed_eq = []
        self.solved_eq = None
        self.node_vars = []
        self.known_vars = []
        self.result = []
        self.circuit = circuit_to_solve
        """:type : Circuit"""
        self.ref = None
        """:type : circuit.Node"""


class Teacher(object):
    """
    Teachers allow us to conveniently and nicely print the information
    created by a Solver. Each step of the solution is explained in an easy and
    straightforward way such that the student can understand it
    """
    def __init__(self, solver):
        self.solver = solver
        """:type : Solver"""

    def explain(self):
        print("First choose a reference voltage (ground node):\nNode {0} is ref at 0V".format(self.solver.solution[-1].ref.node_num))
        print("We then identify the voltage at each node connected to ground.")
        # TODO insert printing of voltages
        print("With this information, we can calculate the current through each resistive branch across which the voltage is known:")
        # TODO insert printing of currents
        print("This allows us to solve some circuits which don't require node voltage or mesh current analysis")
        print("Performing KCL at each node:")
        print(self.solver.solution[-1].node_voltage_eqs_str)
        print("Substituting in for the known variables:")
        print(self.solver.solution[-1].known_vars)
        print("And solving the system of equations using Kramer's rule or equivalent method:")
        print(self.solver.solution[-1].subbed_eqs)
