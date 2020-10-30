import gurobipy as gp
from gurobipy import GRB
import numpy as np

# distance to each gate
gate, distance = gp.multidict({
    'Gate1': 100,
    'Gate2': 200,
    'Gate3': 300,
    })

# capacity of each flight
flight, pax, arrival, departure = gp.multidict({
    'Flight1': [100, 9.00, 9.45],
    'Flight2': [200, 9.30, 10.15],
    'Flight3': [300, 10.00, 10.45],
    })


# aircraft availability
availability = gp.tuplelist([
    ('Flight1', 'Gate1'), ('Flight1', 'Gate2'), ('Flight1', 'Gate3'),
    ('Flight2', 'Gate1'), ('Flight2', 'Gate2'), ('Flight2', 'Gate3'),
    ('Flight3', 'Gate1'), ('Flight3', 'Gate2'), ('Flight3', 'Gate3')
    ])

try:

    # Create a new model
    model = gp.Model("Gate_Planning")

    # Create variables
    x = model.addVars(availability, vtype=GRB.BINARY, name="x")

    # Create objective
    model.setObjective(gp.quicksum(pax[f]*distance[g]*x[f,g] for f, g in availability), GRB.MINIMIZE)

    # Add constraints
    model.addConstrs(x.sum(f,'*') == 1 for f in flight) # 1 gate for 1 flight
    #model.addConstrs(x.sum('*',g) <= 1 for g in gate)   # max 1 flight per gate


    for i in range(1, len(flight)):
        for j in range(1, len(gate)):
            if departure['Flight'+str(i)] > arrival['Flight'+str(i+1)]:
                model.addConstr(x['Flight'+str(i),'Gate'+str(j)] + x['Flight'+str(i+1),
                                                                      'Gate'+str(j)] <= 1)


    # Optimize model
    model.optimize()

    for v in model.getVars():
        print('%s %g' % (v.varName, v.x))

    print('Obj: %g' % model.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')