import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

gate_sheet_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Gates')
flight_sheet_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Flight Schedule')

gate_import = gate_sheet_import['Gate']
distance_import = gate_sheet_import['Walking Distance']
comp_ac_import = gate_sheet_import['Comp. AC']
gate_type_import = gate_sheet_import['Type']
gate_security_import = gate_sheet_import['Security']
flight_import = flight_sheet_import['Flight No.']
PAX_import = flight_sheet_import['Pax']
ETA_import = flight_sheet_import['ETA']
ETD_import = flight_sheet_import['ETD']
AC_import = flight_sheet_import['AC']
sec_in_import = flight_sheet_import['Security In']
sec_out_import = flight_sheet_import['Security Out']
flight_type_import = flight_sheet_import['Type']

types = np.array([['FSNC', 'Jet Bridge'], ['Low-Cost', 'Remote'], ['Business', 'Business']])

gate = []
distance = {}
comp_ac = {}
gate_type = {}
gate_security = {}

for i in range(len(gate_import)):
    gate_x = gate_import[i]
    gate.append(gate_x)
    distance[gate_x] = distance_import[i]
    comp_ac[gate_x] = comp_ac_import[i]
    gate_type[gate_x] = gate_type_import[i]
    gate_security[gate_x] = gate_security_import[i]

flight = []
PAX = {}
ETA = {}
ETD = {}
AC = {}
flight_type = {}
sec_in = {}
sec_out = {}

for j in range(len(flight_import)):
    flight_x = flight_import[j]
    flight.append(flight_x)
    PAX[flight_x] = PAX_import[j]
    ETA[flight_x] = ETA_import[j]
    ETD[flight_x] = ETD_import[j]
    AC[flight_x] = AC_import[j]
    flight_type[flight_x] = flight_type_import[j]
    sec_in[flight_x] = sec_in_import[j]
    sec_out[flight_x] = sec_out_import[j]

errorobj = {}
for flight1 in flight:
    error = []
    for g in range(len(comp_ac_import)):
        if AC[flight1] in comp_ac_import[g] and sec_in[flight1] in gate_security_import[g] and sec_out[flight1] in \
                gate_security_import[g]:
            error.append(1)
        else:
            error.append(0)

    if not 1 in error:
        errorobj[
            flight1] = 'This flight is not supported at the airport as the required gate does not excist! (AC_TYPE or combi with S/NS)'

if not errorobj == {}:
    raise Exception(errorobj)

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables
    x = model.addVars(flight, gate, vtype=GRB.BINARY, name="x")

    # Create objective
    model.setObjective(gp.quicksum(PAX[f] * distance[g] * x[f, g] for f in flight for g in gate), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(x.sum(f, '*') == 1 for f in flight)  # 1 gate for 1 flight

    for f1 in flight:
        for f2 in flight:

            # 2 flights can't be at the same gate at the same time
            if ETD[f1] > ETA[f2] and ETA[f1] < ETD[f2] and not f1 == f2 and flight.index(f1) < flight.index(f2):
                for g in gate:
                    model.addConstr(1 * x[f1, g] + 1 * x[f2, g] <= 1)

        LHS = 0
        for g in gate:

            # Gate should be compatible with aircraft
            if not AC[f1] in comp_ac[g]:
                model.addConstr(1 * x[f1, g] == 0)

            if not sec_in[f1] in gate_security[g]:
                model.addConstr(1 * x[f1, g] == 0)

            if not sec_out[f1] in gate_security[g]:
                model.addConstr(1 * x[f1, g] == 0)

            # Assign flight to the right gate type
            t = np.where(types == flight_type[f1])[0][0]
            if gate_type[g] == types[t][1]:
                LHS += x[f1, g]
        model.addConstr(LHS == 1)

    # Optimize model
    model.optimize()

    for v in model.getVars():
        if not abs(v.x) == 0:
            print('%s %g' % (v.varName, v.x))

    print('Obj: %g' % model.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
