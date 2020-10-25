# -*- coding: utf-8 -*-
"""

Basic Gate Assignment Problem
Created on Fri Oct 23 12:27:04 2020

@author: HJ Hoogendoorn
"""
import numpy as np
import gurobipy as gp
from gurobipy import GRB

# Flight = [ETA, ETD, PAX]
FlightID, ETA, ETD, PAX = gp.multidict({
        'KL1807': [900 ,  945, 100],
        'RA1234': [1100, 1200, 500],
        'KL1724': [930 , 1015, 200],
        'JAC34':  [1505, 1800, 56 ]})


# Gate = Walking distance
Gate, Walkingdis = gp.multidict({
        'B36': 100,
        'C11': 200,
        'D14': 300})



#create a new model
m = gp.Model("BASICGateAssignmentProblemModel")


#create variables
x = m.addVars(FlightID, Gate, vtype=GRB.BINARY, name="x")

objcoef = np.array([])
xvalues = np.array([])
for f in FlightID:
    for g in Gate:
        objcoef = np.append(objcoef, np.array([PAX[f]*Walkingdis[g]]))

for i in x:
    xvalues = np.append(xvalues, np.array([x[i]]), axis=0)

obj = None
for i in range(len(xvalues)):
    obj += objcoef[i]*xvalues[i]
 
    
#Objective
m.setObjective(obj ,GRB.MINIMIZE)

#Add constraints
c0 = None

for f in FlightID:
    for g in Gate:
        c0 += 1*x[f,g]
    m.addConstr(c0 == 1)
    c0 = None
    

for flight1 in FlightID:
    for flight2 in FlightID:
      

        if ETD[flight1] > ETA[flight2] and ETA[flight1] < ETD[flight2] and not flight1 == flight2 and FlightID.index(flight1) < FlightID.index(flight2) :
          
            for g in Gate:
                m.addConstr(1*x[flight1,g] + 1*x[flight2,g] <= 1)
        
        
            
#optimize problem
m.optimize()   
for v in m.getVars():
    if not abs(v.x) == 0:
        print('%s %g' % (v.varName, v.x))
   

print('Obj: %g' % m.objVal)           
            
            
            
            
            
            
            