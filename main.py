__author__ = 'Dany'
__hand_drawn = True
if __hand_drawn:
    from matplotlib import pyplot as plt
    plt.xkcd()
#import SchemDraw as schem
#import SchemDraw.elements as e
import circuit
import components

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

"""
ideas:
renumer nodes so that it matches your solution
define ground so that it matches your solution
solve symbolically then evaluate
"""

#ohms = circuit.Circuit('text')
#ohms = circuit.Circuit('my_circuit')
ohms = circuit.Circuit('node_voltage')
ohms.create_nodes()
ohms.populate_nodes()
ohms.calc_admittance_matrix()
ohms.identify_nontrivial_nodes()
ohms.create_branches()
ohms.create_supernodes()
ohms.sub_super_nodes()
ohms.define_reference_voltage()
ohms.ref = ohms.nodedict[0]
ohms.identify_nontrivial_nonsuper_nodes()
print("First choose a reference voltage (ground node):\nNode {0} is ref at 0V".format(ohms.ref.node_num))
print("Now, for each voltage source connected to this reference, it is easy to determine the voltage at the opposite node")
ohms.identify_voltages()
print("With this information, we can calculate the current through each resistive branch across which the voltage is known:")
ohms.identify_currents()
print("Performing KCL at each of the nodes in the circuit:")
#ohms.kcl_everywhere()
#ohms.ohms_law_where_easy()
ohms.gen_node_voltage_eq()
#print(ohms.nodelist)
#print(ohms.num_nodes)
#print(ohms.netlist)
ohms.printer()
#print(ohms.numerators)
#print(ohms.denomenators)
