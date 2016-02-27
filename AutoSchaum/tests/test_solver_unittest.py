from nose2.compat import unittest
from AutoSchaum.AutoSchaum import solver, circuit

class SolverTest(unittest.TestCase):
    def setUp(self):
        self.my_circuit = circuit.Circuit("AutoSchaum/resources/my_circuit.crt")
        self.my_circuit.create_nodes()
        self.my_circuit.populate_nodes()
        self.my_solver = solver.Solver(self.my_circuit)
        self.my_solver.solution[-1].ref = self.my_solver.circuit.nodedict[0]
        self.my_other_circuit = circuit.Circuit("AutoSchaum/resources/node_voltage.crt")
        self.my_other_circuit.create_nodes()
        self.my_other_circuit.populate_nodes()
        self.my_other_solver = solver.Solver(self.my_other_circuit)
        self.my_other_solver.solution[-1].ref = self.my_other_solver.circuit.nodedict[0]
        
    def tearDown(self):
        pass
    
    def test_identify_voltage(self):
        self.my_solver.identify_voltages()
        self.assertEqual(self.my_solver.circuit.nodedict[0].voltage, 0)
        self.assertEqual(self.my_solver.circuit.nodedict[1].voltage, 1)
        self.assertEqual(self.my_solver.circuit.nodedict[2].voltage, 5)
        self.assertEqual(self.my_other_solver.circuit.nodedict[2].voltage, 10)
        
if __name__ == '__main__':
    unittest.main()

