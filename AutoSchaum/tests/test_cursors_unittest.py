from nose2.compat import unittest
import AutoSchaum.AutoSchaum.cursors as cursors
import AutoSchaum.AutoSchaum.circuit as circuit

def components_to_refdesigs(component_list):
    return [x.refdes for x in component_list]

class CircuitTest(unittest.TestCase):
    def setUp(self):
        self.my_circuit = circuit.Circuit("AutoSchaum/resources/my_circuit.crt")

    def test_create_nodes(self):
        self.my_circuit.create_nodes()
        self.assertEqual(3,
                         len(self.my_circuit.nodedict))
        for node in self.my_circuit.nodedict.values():
            self.assertIsInstance(node, circuit.Node)
        
class CursorTest(unittest.TestCase):
    def setUp(self):
        self.my_node = circuit.Node(0)
        self.my_empty_cursor = cursors.Cursor(self.my_node)
        self.my_circuit = circuit.Circuit("AutoSchaum/resources/my_circuit.crt")
        self.my_circuit.create_nodes()
        self.my_circuit.populate_nodes()
        self.my_cursor = cursors.Cursor(self.my_circuit.nodedict[0])

    def test_step_to(self):
        self.assertEqual(["R1", "R2", "V1"],
                         components_to_refdesigs(self.my_cursor.step_to(self.my_circuit.nodedict[1])))
        self.assertEqual(self.my_circuit.nodedict[1],
                         self.my_cursor.last_node_seen())
        self.assertEqual(self.my_cursor.location, self.my_circuit.nodedict[1])
        
    def test_unseen(self):
        self.assertEqual(self.my_circuit.component_list,
                         self.my_cursor.unseen(self.my_circuit.component_list))
        self.my_cursor.step_to(self.my_circuit.nodedict[1])
        self.assertEqual(components_to_refdesigs(self.my_cursor.unseen(self.my_circuit.component_list)),
                         ["V2"])
        self.my_cursor.step_to(self.my_circuit.nodedict[0])
        self.assertEqual(components_to_refdesigs(self.my_cursor.unseen(self.my_circuit.component_list)),
                         ["V2"])
        
    def test_unseen_connected(self):
        self.assertEqual(["R1", "R2", "V1"],
                         [x.refdes for x in self.my_cursor.unseen_connected()])
        self.my_cursor.step_to(self.my_circuit.nodedict[1])
        self.assertEqual(["V2"],
                         [x.refdes for x in self.my_cursor.unseen_connected()])
        self.my_cursor.step_to(self.my_circuit.nodedict[0])
        self.assertEqual([],
                         self.my_cursor.unseen_connected())

    def test_step_along(self):
        first_seen = self.my_cursor.step_along(self.my_circuit.nodedict[1])
        self.assertEqual(self.my_cursor.location, self.my_circuit.nodedict[1])
        self.assertEqual("R1", first_seen.refdes)
        second_seen = self.my_cursor.step_along(self.my_circuit.nodedict[0])
        self.assertEqual(self.my_cursor.location, self.my_circuit.nodedict[0])
        self.assertEqual("R2", second_seen.refdes)

        
if __name__ == '__main__':
    unittest.main()
