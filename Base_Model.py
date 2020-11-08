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
reg = []
AC = {}
flight_in = {}
PAX_in = {}
sec_in = {}
ETA = {}
flight_out = {}
PAX_out = {}
sec_out = {}
ETD = {}

for r in range(len(flight_import)):
    reg_i = flight_import['Registration'][r]
    reg.append(reg_i)

    AC[reg_i] = flight_import['AC'][r]
    flight_in[reg_i] = flight_import['Flight No. In'][r]
    PAX_in[reg_i] = flight_import['Pax In'][r]
    sec_in[reg_i] = flight_import['Security In'][r]
    ETA[reg_i] = flight_import['ETA'][r]
    flight_out[reg_i] = flight_import['Flight No. Out'][r]
    PAX_out[reg_i] = flight_import['Pax Out'][r]
    sec_out[reg_i] = flight_import['Security Out'][r]
    ETD[reg_i] = flight_import['ETD'][r]

# Process transfer data


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
for r in reg:
    error = []
    for g in gate:
        if AC[r] in comp_ac[g] and sec_in[r] in gate_security[g] and sec_out[r] in gate_security[g]:
            error.append(1)
        else:
            error.append(0)

    if not 1 in error:
        errorobj[
            r] = 'This flight is not supported at the airport as the required gate does not excist! (AC_TYPE or combi with S/NS)'

if not errorobj == {}:
    raise Exception(errorobj)


'''
Set up the model
'''

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables
    x = model.addVars(reg, gate, vtype=GRB.BINARY, name="x")

    # Create objective
    model.setObjective(gp.quicksum(PAX_in[r]*distance[g] * x[r,g] for r in reg for g in gate), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(x.sum(r,'*') == 1 for r in reg)  # 1 gate for 1 flight

    # Loop over all flights
    for r1 in reg:
        a_code = flight_in[r1].strip('0123456789')
        lhs = 0

        # Loop over all gates
        for g in gate:
            pier = g.strip('0123456789')

            # Gate should be compatible with aircraft
            if not AC[r1] in comp_ac[g]:
                model.addConstr(1*x[r1,g] == 0)

            # Check security compatibility incoming flight
            if not sec_in[r1] in gate_security[g]:
                model.addConstr(1*x[r1,g] == 0)

            # Check security compatibility outgoing flight
            if not sec_out[r1] in gate_security[g]:
                model.addConstr(1*x[r1,g] == 0)

            # Aircraft should be parked at the right pier
            if pier in airline_pier[a_code]:
                lhs += 1*x[r1,g]
        model.addConstr(lhs == 1)

        for r2 in reg:

            # 2 flights can't be at the same gate at the same time
            if ETD[r1] > ETA[r2] and ETA[r1] < ETD[r2] and not r1 == r2 and reg.index(r1) < reg.index(r2):
                for g in gate:
                    model.addConstr(1*x[r1,g] + 1*x[r2,g] <= 1)

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
