#!/usr/bin/env python
"""
Hourly Optimizer for a full year


Returns: Energy demand for every hour 
"""

import gurobi as gb
from gurobipy import GRB

import networkx as nx
import numpy as np
#import math

import json
from statistics import mean 
import pandas as pd

import sys
import csv
import itertools

import sys 
import os
sys.path.append(os.path.abspath("/home/k/projects/CA_microservices"))
from lib import *

# Command-Line Arguments
#cliArg = sys.argv[1:]
#energyBudget = float(cliArg[0])
#userDemand = float(cliArg[1])




def optimizationHourly(energyBudget, user_demand, indices, userMax, energyDemand, q):
    """
    Find optimal configuration for a given energy budget and user demand

    :param p1: energy budget
    :param p2: user demand
    :param p3: indices of configuration options (for the iterations)
    :param p4: dataset of maximum users per configuration option
    :param p5: dataset of energy demand per configuration option
    :param p6: dataset of throughput per configuration option
    :return: energy demand for optimal configuration
    """ 
    shape = [(ms,x) for ms in range(len(indices)) for x in range(len(indices[ms]))]
    # Create optimization model
    m = gb.Model('ca_microservice_global')

    # Creates the Gurobi Variable from the list of lists 
    b = m.addVars(shape, vtype=GRB.BINARY, name="b")

    # User-Troughput Variable (e.g., QoS, QoE, Revenue, etc.)
    # 1.0 indicates 100% users getting to next component in the workflow
    u = m.addVars(len(indices)+1, lb=0.0, vtype=GRB.CONTINUOUS, name="u") # ub=20.0 unnecessary?

    # Scaling Factor. Indicates how many instances are needed to serve the user demand. For each microservice
    sf = m.addVars(shape, lb=0, vtype=GRB.INTEGER, name="sf")
    m.update()
    # Binary constraint for the configuration picking. Ensures that only one execution format is picked for each microservice
    # ToDo: Ensure that mandatory/core microservices always have one execution format running

    #for ms in range(len(indices)):
        
    # Scaling Factor constraint

    for ms in range(len(indices)):
        m.addConstr(sum(b[ms,x] for x in range(len(indices[ms]))) == 1, name="c-ms"+str(ms))
        for x in range(len(indices[ms])):
            if userMax[ms][x] == 10000000000:
                m.addConstr(sf[ms,x] == 0, name="c-sf"+str(ms)+str(x))
            else:
                m.addConstr(userMax[ms][x]*sf[ms,x] >= u[ms]*user_demand, name="c-sf"+str(ms)+str(x))
            #m.addConstr(2*(userMax[ms][x])*sf[ms,x] <= u[ms]*user_demand , name="c-sf")
        # Energy Budget Constraint
        # Indicator constraints
    m.addConstr(sum(b[ms,x]*energyDemand[ms][x]*sf[ms,x] for ms in range(len(indices)) for x in range(len(indices[ms])) ) <= energyBudget, name="c-eb")
                

    # User-Throughput Constraint
    m.addConstr(u[0] == 1, name="c-q-initial")
    for ms in range(0,len(indices)):
        m.addConstr(u[ms] * sum(b[ms,x] * q[ms][x] for x in range(len(indices[ms]))) == u[ms+1], name="c-q"+str(ms))
    #m.addConstr(u[len(indices)] == u[len(indices)+1], name="c-q-last")

    m.update()
    #obj = gb.quicksum(b[ms,x]*q[ms][x] for ms in range(len(indices)) for x in range(len(indices[ms]))) # or u[len(indices)] ?
    m.setObjective(u[len(indices)], GRB.MAXIMIZE)
    # Compute optimal solution
    m.params.NonConvex = 2
    m.optimize()


    # Print solution
    row = []
    row.append([var.X for var in m.getVars() if "u" in var.VarName][5])
    row.append([var.X for var in m.getVars() if "u" in var.VarName][5] * user_demand)

    ed = 0
    execFormats = [var.X for var in m.getVars() if "b" in var.VarName]
    scalingFactor = [var.X for var in m.getVars() if "sf" in var.VarName]
    energyDemand_flat = [item for sublist in energyDemand for item in sublist]

    for i in range(len(execFormats)):
        ed += execFormats[i]*scalingFactor[i]*energyDemand_flat[i]
    row.append(ed)

    f = open('/home/k/projects/CA_microservices/results/optimization_result.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()
    return(ed)

data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('/home/k/projects/CA_microservices/flightBooking.json')

df = pd.read_csv(r'../data/DE_2020.csv')
ci_data = df['carbon_intensity_avg']

df = pd.read_csv(r'../data_scraping/projectcount_wikiDE_2014.csv')
clickData_hourly_2014 = df["de"]
energyBudget = calcCarbonBudgetHourInWeekAVG(2014,clickData_hourly_2014,ci_data)

year=2015
weekday_frequency = weekdayfrequency(year)
s = weekday_frequency.index(53)*24


indices = []
for ms in data['components']:
    indices.append([0] * len(data['components'][ms]))

df = pd.read_csv(r'../data_scraping/projectcount_wikiDE-de.csv')
clickData_hourly = df["De"]
for t in range(len(clickData_hourly)):
    index = (t+s)%168
    optimizationHourly(energyBudget[index], clickData_hourly[t], indices, userMax, energyDemand, q)