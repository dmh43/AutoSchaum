__author__ = 'Dany'
""" Each circuit is represented by a netlist where each line has the following format:
        [component refdes] [list of nodes to connect to] [value]
    Component Types:
        -Resistor 'R'
        -Capacitor 'C'
        -Inductor 'L'
        -Complex Impedance 'Z'
        -Voltage source 'V'
        -Current source 'I'
        -Voltage Controlled voltage source 'VCVS'
        -Current controlled voltage source 'CCVS'
        -Voltage controlled current source 'VCIS'
        -Current controlled current source 'CCIS'
    Default units are:
        -Impedance: Ohms
        -Voltage source: V
        -Current Source: A
    Each circuit has a corresponding admittance matrix and current injection vector:
        I = YV; where I and V are vectors and Y is a matrix
"""

from components import *

class Circuit:
    def __init__(self, netlist_filename):
        netlist = open('netlist_filename', 'r')
        self.name = netlist.readline()
        while True:
            #do while loop which looks for first component in netlist
            __nextline = netlist.readline()
            if __nextline[0] in component_types: #first letter tells us component list started
                break
    def __calc_admittance(self):
#write wrapper for dealing with tuples representing complex numbers!