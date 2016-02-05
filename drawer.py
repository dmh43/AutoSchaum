import SchemDraw as schem
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
        while self._state: # TODO Add real stack ability
            self.pop()
            schem_cursor.step_back()
            schem_cursor.draw_comps_here('down')
        self.draw()
        self.save('resources/khiri.png')


class DrawerCursor(cursors.Cursor):
    """
    This cursor helps draw schematics.
    """
    # TODO Make this a better, more consistent wrapper. So that push and pop happens together
    def __init__(self, schematic):
        super(DrawerCursor, self).__init__(schematic.circuit.nodedict[0])
        self.schem = schematic
        """:type : Schematic"""

    def draw_comps_here(self, direc='right'):
        if self.unseen_connected():
            if self.unseen_connected() > 1:
                self.schem.push()
            new_comps = self.step_down_unseen_comp()
            direction = direc
            if len(new_comps) > 1: # for elements in parallel
                for comp in new_comps:
                    self.schem.push()
                    self.schem.add(comp.schem_sym, d=direction, botlabel='${0}$'.format(comp.refdes))
                    self.schem.pop()
            elif len(new_comps) == 1:
                comp = new_comps[0]
                self.schem.add(comp.schem_sym, d=direction, botlabel='${0}$'.format(comp.refdes))
            return new_comps
        else:
            return []
