import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd


'''
Importing data
'''

# Import the data from the excel file
gate_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Gates')
flight_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Flight Schedule')
airline_import = pd.read_excel('Gate_Planning.xlsx', sheet_name='Airlines')

# Process flight data
flight = []
PAX = {}
ETA = {}
ETD = {}
AC = {}
sec_in = {}
sec_out = {}

for f in range(len(flight_import)):
    flight_i = flight_import['Flight No.'][f]
    flight.append(flight_i)

    PAX[flight_i] = flight_import['Pax'][f]
    ETA[flight_i] = flight_import['ETA'][f]
    ETD[flight_i] = flight_import['ETD'][f]
    AC[flight_i] = flight_import['AC'][f]
    sec_in[flight_i] = flight_import['Security In'][f]
    sec_out[flight_i] = flight_import['Security Out'][f]

# Process gate data
gate = []
distance = {}
comp_ac = {}
gate_type = {}
gate_security = {}

for g in range(len(gate_import)):
    gate_j = gate_import['Gate'][g]
    gate.append(gate_j)

    distance[gate_j] = gate_import['Walking Distance'][g]
    comp_ac[gate_j] = gate_import['Comp. AC'][g]
    gate_security[gate_j] = gate_import['Security'][g]

# Process airline data
airline = []
airline_code = {}
airline_pier = {}

for a in range(len(airline_import)):
    airline_a = airline_import['Airline Code'][a]
    airline.append(airline_a)

    airline_code[airline_a] = airline_import['Airline Name'][a]
    airline_pier[airline_a] = airline_import['Pier'][a]

# Check for errors
errorobj = {}
for f in flight:
    error = []
    for g in gate:
        if AC[f] in comp_ac[g] and sec_in[f] in gate_security[g] and sec_out[f] in gate_security[g]:
            error.append(1)
        else:
            error.append(0)

    if not 1 in error:
        errorobj[
            f] = 'This flight is not supported at the airport as the required gate does not excist! (AC_TYPE or combi with S/NS)'

if not errorobj == {}:
    raise Exception(errorobj)


'''
Set up the model
'''

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables
    x = model.addVars(flight, gate, vtype=GRB.BINARY, name="x")

    # Create objective
    model.setObjective(gp.quicksum(PAX[f] * distance[g] * x[f, g] for f in flight for g in gate), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(x.sum(f, '*') == 1 for f in flight)  # 1 gate for 1 flight

    # Loop over all flights
    for f1 in flight:
        a_code = f1.strip('0123456789')
        lhs = 0

        # Loop over all gates
        for g in gate:
            pier = g.strip('0123456789')

            # Gate should be compatible with aircraft
            if not AC[f1] in comp_ac[g]:
                model.addConstr(1*x[f1,g] == 0)

            # Check security compatibility incoming flight
            if not sec_in[f1] in gate_security[g]:
                model.addConstr(1*x[f1,g] == 0)

            # Check security compatibility outgoing flight
            if not sec_out[f1] in gate_security[g]:
                model.addConstr(1*x[f1,g] == 0)

            # Aircraft should be parked at the right pier
            if pier in airline_pier[a_code]:
                lhs += 1*x[f1,g]
        model.addConstr(lhs == 1)

        for f2 in flight:

            # 2 flights can't be at the same gate at the same time
            if ETD[f1] > ETA[f2] and ETA[f1] < ETD[f2] and not f1 == f2 and flight.index(f1) < flight.index(f2):
                for g in gate:
                    model.addConstr(1*x[f1,g] + 1*x[f2,g] <= 1)

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
