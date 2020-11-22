import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

'''
Functions
'''

def get_registration(dictionary,flight_no):
    i = list(dictionary.values()).index(flight_no)
    r = list(dictionary.keys())[i]
    return r

def hour_fraction(time):
    hours = time.hour
    minutes = time.minute
    seconds = time.second
    new_time = hours + minutes/60 + seconds/3600
    return new_time

'''
Importing data
'''

file_name = 'Gate_Planning.xlsx'

# Model used for verification?
verification = False

# Import the data from the excel file
flight_import = pd.read_excel(file_name, sheet_name='Flight Schedule')
transfer_import = pd.read_excel(file_name, sheet_name='Transfers')
gate_import = pd.read_excel(file_name, sheet_name='Gates')
pier_import = pd.read_excel(file_name, sheet_name='Piers')
pier_passport_import = pd.read_excel(file_name, sheet_name='Passport Control')
airline_import = pd.read_excel(file_name, sheet_name='Airlines')
buffer_import = pd.read_excel(file_name, sheet_name='Buffer Time')

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
    ETA[reg_i] = hour_fraction(flight_import['ETA'][r])
    flight_out[reg_i] = flight_import['Flight No. Out'][r]
    PAX_out[reg_i] = flight_import['Pax Out'][r]
    sec_out[reg_i] = flight_import['Security Out'][r]
    ETD[reg_i] = hour_fraction(flight_import['ETD'][r])

# Process transfer data
arr_flight = []
dep_flight = []
PAX_transfer = {}
PAX_transfer_t = {}

for p in range(len(transfer_import)):
    arr_flight_p = transfer_import['Arriving Flight'][p]
    dep_flight_p = transfer_import['Departing Flight'][p]
    arr_flight.append(arr_flight_p)
    dep_flight.append(dep_flight_p)

    reg_arr = get_registration(flight_in,arr_flight_p)
    reg_dep = get_registration(flight_out,dep_flight_p)

    PAX_transfer[reg_arr,reg_dep] = transfer_import['PAX'][p]

    if reg_arr in PAX_transfer_t:
        PAX_transfer_t[reg_arr] += transfer_import['PAX'][p]
    else:
        PAX_transfer_t[reg_arr] = transfer_import['PAX'][p]
    if reg_dep in PAX_transfer_t:
        PAX_transfer_t[reg_dep] += transfer_import['PAX'][p]
    else:
        PAX_transfer_t[reg_dep] = transfer_import['PAX'][p]

# Process gate data
gate = []
distance = {}
comp_ac = {}
gate_security = {}

for g in range(len(gate_import)):
    gate_j = gate_import['Gate'][g]
    gate.append(gate_j)

    distance[gate_j] = gate_import['Walking Distance'][g]
    comp_ac[gate_j] = gate_import['Comp. AC'][g]
    if gate_import['Security'][g] == 'S' or gate_import['Security'][g] == 'N':
        gate_security[gate_j] = gate_import['Security'][g]
    else:
        gate_security[gate_j] = 'NS'

# Process pier data
pier = []
pier_distance = {}

for p in range(len(pier_import)):
    pier_in = pier_import['From'][p]
    pier_out = pier_import['To'][p]

    if pier_in not in pier:
        pier.append(pier_in)
    if pier_out not in pier:
        pier.append(pier_out)

    pier_distance[pier_in,pier_out] = pier_import['Distance'][p]

for p1 in pier:
    for p2 in pier:
        if p1 != p2 and (p1,p2) not in pier_distance:
            if p2 == 'A':
                pier_distance[p1,p2] = pier_distance[p2,p1]
            else:
                pier_distance[p1,p2] = abs(pier_distance['A',p1]-pier_distance['A',p2])

# Process airline data
airline = []
airline_code = {}
airline_pier = {}

for a in range(len(airline_import)):
    airline_a = airline_import['Airline Code'][a]
    airline.append(airline_a)

    airline_code[airline_a] = airline_import['Airline Name'][a]
    airline_pier[airline_a] = airline_import['Pier'][a]

# Process passport control data
pier_passport = []

for p in range(len(pier_passport_import)):
    pier_passport_p = pier_passport_import['Pier'][p]
    pier_passport.append(pier_passport_p)

    pier_distance[pier_passport_p,pier_passport_p] = 2*pier_passport_import['Distance'][p]



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



# Process buffer time data
tb = buffer_import['Buffer Time (minutes)'][0]/60


'''
Set up the model
'''

gate_usage = [0] * len(gate)

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables

    # Create gate allocation variables
    x = model.addVars(reg, gate, vtype=GRB.BINARY, name="x")

    # Transfers
    t = {}
    obj_transfer = 0
    # Loop over all arriving flight with transfer pax
    for f in range(len(arr_flight)):
        f1 = arr_flight[f]
        f2 = dep_flight[f]

        # Determine ac registration arriving flight
        r1 = get_registration(flight_in,f1)
        r2 = get_registration(flight_out,f2)

        for g1 in gate:
            # Determine pier
            p1 = g1.strip('0123456789')
            for g2 in gate:
                # Determine pier
                p2 = g2.strip('0123456789')
                if (p1 == p2 and sec_in[r1] != sec_out[r2]) or p1 != p2:
                    # Create variable
                    t[r1,g1,r2,g2] = model.addVar(ub=1,vtype=GRB.BINARY,name="t[%s,%s,%s,%s]"%(r1,g1,r2,g2))
                    # Add constraint
                    model.addConstr(1*x[r1,g1] + 1*x[r2,g2] - t[r1,g1,r2,g2] <= 1)
                    # Contribution to objective
                    obj_transfer += PAX_transfer[r1,r2]*pier_distance[p1,p2]*t[r1,g1,r2,g2]

    # Determine amount of passengers
    PAX = {}
    for r in reg:
        if r in PAX_transfer_t:
            PAX[r] = PAX_in[r] + PAX_out[r] - PAX_transfer_t[r]
        else:
            PAX[r] = PAX_in[r] + PAX_out[r]

    # Create objective
    model.setObjective(gp.quicksum(PAX[r]*distance[g] * x[r,g] for r in reg for g in gate) + obj_transfer, GRB.MINIMIZE)

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
            if (ETD[r1]+tb) > ETA[r2] and ETA[r1] < (ETD[r2]+tb) and not r1 == r2 and reg.index(r1) < reg.index(r2):
                for g in gate:
                    model.addConstr(1*x[r1,g] + 1*x[r2,g] <= 1)

    # Optimize model
    model.optimize()

    for v in model.getVars():
        if not abs(v.x) == 0:
            print('%s %g' % (v.varName, v.x))
            if v.varName[0] == 'x' and not verification:
                if v.varName[9] == ',':
                    gate_string = str(v.varName[10:12])
                    reg_string = str(v.varName[2:9])
                elif v.varName[8] == ',':
                    gate_string = str(v.varName[9:11])
                    reg_string = str(v.varName[2:8])

                index = gate.index(gate_string)
                gate_usage[index] += (ETD[reg_string] - ETA[reg_string])

    print('Obj: %g' % model.objVal)

    #print(gate_usage)

    gate_usage_array = (np.array(gate_usage))/7
    total_gate_usage = np.average(gate_usage_array)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')