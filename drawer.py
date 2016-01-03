import SchemDraw as schem
import SchemDraw.elements as e
import cursors


class Schematic(schem.Drawing):
    """Wrapper for SchemDraw Drawing class"""
    def __init__(self, circuit):
        super(Schematic, self).__init__()
        self.circuit = circuit

    def draw_schem(self):
        """Draw the schematic automatically"""
        schem_cursor = DrawerCursor(self)
        while schem_cursor.draw_comps_here():
            pass
        self.draw()
        self.save('khiri.png')


class DrawerCursor(cursors.Cursor):
    """
    This cursor helps draw schematics
    """
    def __init__(self, schematic):
        super(DrawerCursor, self).__init__(schematic.circuit.nodedict[0])
        self.schem = schematic
        """:type : Schematic"""

    def draw_comps_here(self):
         new_comps = self.step_down_unseen_comp()
         direction = 'right' # TODO Change this for more complex drawings
         if len(new_comps) > 1:
             for comp in new_comps:
                 self.schem.push()
                 self.schem.add(comp.schem_sym, d=direction, botlabel='${0}$'.format(comp.refdes))
                 self.schem.pop()
         elif len(new_comps) == 1:
             comp = new_comps[0]
             self.schem.add(comp.schem_sym, d=direction, botlabel='${0}$'.format(comp.refdes))
         return new_comps
