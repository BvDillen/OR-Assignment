'''

Basic Gate Planning Model

'''

# Necessary imports
from gurobipy import Model,GRB,LinExpr
import time
import pandas as pd


'''
Model Parameters
'''

# File, sheet and column names
file_name = 'Gate_Planning.xlsx'

gate_sheet = 'Gates'
flights_sheet = 'Flight Schedule'

flight_name = 'Flight No.'
pax_name = 'Pax'
arrival_name = 'ETA'
departure_name = 'ETD'
gate_name = 'Gate'
distance_name = 'Walking Distance'

# Import data

gates = pd.read_excel(file_name,sheet_name=gate_sheet)
# Number of gates
n_gates = len(gates)

flights = pd.read_excel(file_name,sheet_name=flights_sheet)
# Number of flights
n_flights = len(flights)


# Initiate empty model
time_start = time.time()
model = Model()


'''
Variables
'''

# x_ij
#   i: Flight
#   j: Gate

x = {}
for i in range(n_flights):
    for j in range(n_gates):
        x[i,j] = model.addVar(ub=1,vtype=GRB.INTEGER,name='x[%s,%s]'%(flights[flight_name][i],gates[gate_name][j]))

# Update model
model.update()


'''
Constraints
'''

# Flights can only be allocated to one gate

# Loop over all the flights
for i in range(n_flights):
    LHS = LinExpr()

    # Loop over every gate
    for j in range(n_gates):
        LHS += x[i,j]

    model.addConstr(lhs=LHS,sense=GRB.EQUAL,rhs=1)


# Every gate can only accommodate one aircraft at a time

# Loop over every flight
for i in range(n_flights):
    t_arr = flights[arrival_name][i]
    t_dep = flights[departure_name][i]

    # Loop over the other aircraft
    for k in range(i+1,n_flights):

        # Check if other flights are at the airport at the same time
        if t_dep>flights[arrival_name][k] and t_arr<flights[departure_name][k]:

            # Add the constraint for every gate
            for j in range(n_gates):
                LHS = LinExpr()
                LHS += x[i,j] + x[k,j]
                model.addConstr(lhs=LHS, sense=GRB.LESS_EQUAL, rhs=1)


# Update model
model.update()


'''
Objective Function
'''

obj = LinExpr()

# Loop over every flight
for i in range(n_flights):

    # Loop over every gate
    for j in range(n_gates):

        # Add "cost" times variables to the objective function
        obj += flights[pax_name][i]*gates[distance_name][j]*x[i,j]

# Set objective
model.setObjective(obj,GRB.MINIMIZE)

# Update the model
model.update()


'''
Solve
'''

# Write .lp file
#model.write('Basic_Model.lp')

# Optimize the model
model.optimize()
time_end = time.time()

print('\nSolved in',round(time_end-time_start,4),'seconds\n')

# Save and print solution
solution = []
for v in model.getVars():
    solution.append([v.varName,v.x])
    if v.x == 1.0:
        print(v.varName,'=',v.x)