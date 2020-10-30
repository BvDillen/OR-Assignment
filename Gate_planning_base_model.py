import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

gate_sheet_import = pd.read_excel('Gate_Planning.xlsx',sheet_name='Gates')
flight_sheet_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Flight Schedule')

gate_import = gate_sheet_import['Gate']
distance_import = gate_sheet_import['Walking Distance']
flight_import = flight_sheet_import['Flight No.']
PAX_import = flight_sheet_import['Pax']
ETA_import = flight_sheet_import['ETA']
ETD_import = flight_sheet_import['ETD']

gate = []
distance = {}

for i in range(len(gate_import)):
    gate_x = gate_import[i]
    gate.append(gate_x)
    distance[gate_x] = distance_import[i]

flight = []
PAX = {}
ETA = {}
ETD = {}

for j in range(len(flight_import)):
    flight_x = flight_import[j]
    flight.append(flight_x)
    PAX[flight_x] = PAX_import[j]
    ETA[flight_x] = ETA_import[j]
    ETD[flight_x] = ETD_import[j]

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables
    x = model.addVars(flight, gate, vtype=GRB.BINARY, name="x")

    # Create objective
    model.setObjective(gp.quicksum(PAX[f]*distance[g]*x[f,g] for f in flight for g in gate), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(x.sum(f,'*') == 1 for f in flight) # 1 gate for 1 flight

    for flight1 in flight:
        for flight2 in flight:

            if ETD[flight1] > ETA[flight2] and ETA[flight1] < ETD[flight2] and not flight1 == flight2 and flight.index(flight1) < flight.index(flight2):
                for g in gate:
                    model.addConstr(1 * x[flight1, g] + 1 * x[flight2, g] <= 1)

    # Optimize model
    model.optimize()

    for v in model.getVars():
        print('%s %g' % (v.varName, v.x))

    print('Obj: %g' % model.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
