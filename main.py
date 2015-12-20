__author__ = 'Dany'
__handdrawn__ = True
if __handdrawn__:
    from matplotlib import pyplot as plt
    plt.xkcd()
#import SchemDraw as schem
#import SchemDraw.elements as e
import circuit
import components
import sympy

# d = schem.Drawing(fontsize=10)
# V1 = d.add(e.SOURCE_V, label='$V_1$=10V')
# R1 = d.add(e.RES, d='right', label='$R_1$=100K$\Omega$')
# V2 = d.add(e.SOURCE_CONT_V, d='down', label='$V_2=V_1\cdot100$')
# R2 = d.add(e.RES, d='left', label='$R_2=50K\Omega$')
# l1 = d.add(e.LINE, to=V1.start)
# R3 = d.add(e.RES, to=R1.end, label='$R_3=20K\Omega$')
# d.add(e.GND, xy=l1.center)
# d.draw()
# d.save('testschematic.png', dpi = 300)

#ohms = circuit.Circuit('text')
#ohms = circuit.Circuit('my_circuit')
ohms = circuit.Circuit('node_voltage')
ohms.load_netlist(open('node_voltage.crt', 'r'))
ohms.create_nodes()
ohms.populate_nodes()
ohms.calc_admittance_matrix()
ohms.identify_nontrivial_nodes()
ohms.create_branches()
ohms.create_supernodes()
ohms.sub_super_nodes() #this should be in Solver
ohms.define_reference_voltage() # this should be in Solver
ohms.ref = ohms.nodedict[0]
ohms.identify_nontrivial_nonsuper_nodes() #this should be in solver
print("First choose a reference voltage (ground node):\nNode {0} is ref at 0V".format(ohms.ref.node_num))
print("Now, for each voltage source connected to this reference, it is easy to determine the voltage at the opposite node")
my_solution = circuit.Solver(ohms)
my_solution.identify_voltages()
print("With this information, we can calculate the current through each resistive branch across which the voltage is known:")
my_solution.identify_currents()
print("Performing KCL at each of the nodes in the circuit:")
#ohms.kcl_everywhere()
#ohms.ohms_law_where_easy()
my_solution.gen_node_voltage_eq()
#ohms.sub_zero_for_ref()
my_solution.determine_known_vars()
my_solution.sub_into_eqs()
my_solution.solve_eqs()
print my_solution.solution[-1].solved_eq
print my_solution.solution[-1].result
#print(ohms.nodelist)
#print(ohms.num_nodes)
#print(ohms.netlist)
my_solution.printer()
#print(ohms.numerators)
#print(ohms.denomenators)
