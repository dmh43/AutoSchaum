import circuit
import solver
import drawer

def main():
    __handdrawn__ = True
    if __handdrawn__:
        from matplotlib import pyplot as plt
        plt.xkcd()

    ohms = circuit.Circuit('resources/node_voltage.crt')
    ohms.create_nodes()
    ohms.populate_nodes()
    ohms.identify_nontrivial_nodes()
    ohms.create_branches()
    ohms.create_supernodes()
    ohms.sub_super_nodes()
    ohms.identify_nontrivial_nonsuper_nodes() # TODO some of these should be moved to solver later
    schem = drawer.Schematic(ohms)
    schem.draw_schem()
    my_solution = solver.Solver(ohms)
    my_solution.set_reference_voltage(my_solution.circuit.non_trivial_reduced_nodedict[0])
    my_solution.identify_voltages()
    my_solution.identify_currents()
    #print("performing kcl at each of the nodes in the circuit:") #todo move to solver
    #ohms.kcl_everywhere()
    #ohms.ohms_law_where_easy()
    my_solution.gen_node_voltage_eq()
    #ohms.sub_zero_for_ref()
    my_solution.determine_known_vars()
    my_solution.sub_into_eqs()
    my_solution.solve_subbed_eqs()
    #print(ohms.nodelist)
    #print(ohms.num_nodes)
    #print(ohms.netlist)
    vivias = solver.Teacher(my_solution)
    vivias.explain()
    #print(ohms.numerators)
    #print(ohms.denomenators)

if __name__ == "__main__":
    main()
