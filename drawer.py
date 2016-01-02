import SchemDraw as schem
import SchemDraw.elements as e

class Schematic(schem.Drawing):
    """Wrapper for SchemDraw Drawing class"""
    def __init__(self, circuit):
        super(Schematic, self).__init__()
        self.circuit = circuit

    def draw_schem(self):
        """Draw the schematic automatically"""
        for comp in self.circuit.component_list: # TODO implement automatic drawing
            print comp.refdes