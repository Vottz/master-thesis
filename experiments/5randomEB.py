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
path = os.path.dirname(os.getcwd())
sys.path.append(path)
from lib import *
import random as rd

# Command-Line Arguments
#cliArg = sys.argv[1:]
#energyBudget = float(cliArg[0])
#userDemand = float(cliArg[1])


def randomEB(hourly_eb):
    n = rd.uniform(1,1.4)
    return (hourly_eb * float(str(n)[:5]))



row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/5_randomEB_optimization_result_075_15.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()


data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('/home/k/projects/CA_microservices/flightBooking.json')
df = pd.read_csv(r'../data/projectcount_wikiDE_2015.csv')
clickData_hourly = df["De"].tolist()
clickData_hourly = clickData_hourly[24:] + clickData_hourly[0:24]


df = pd.read_csv(r'../data/DE_2020.csv')
ci_data = df['carbon_intensity_avg']
df = pd.read_csv(r'../data/projectcount_wikiDE_2014.csv')
clickData_hourly_2014 = df["de"]
carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)


df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021 = df['carbon_intensity_avg']


indices = []
for ms in data['components']:
    indices.append([0] * len(data['components'][ms]))


weekday_frequency = weekdayfrequency(2021)
s = weekday_frequency.index(53)*24

for t in range(len(clickData_hourly)):
    index = (t+s)%168
    eb = randomEB(carbonBudget[index]/ci_data_2021[t])
    qValue,userThrougput,ed = calcED_LP(userMax, energyDemand, q, clickData_hourly[t])
    if ed < eb:
        qValue,userThrougput,ed = optimizationHourly(eb, clickData_hourly[t], indices, userMax, energyDemand, q)
    ce = ed * ci_data_2021[t]
    row = [qValue,userThrougput,ed,eb, clickData_hourly[t], ce]
    f = open('../results/5_randomEB_optimization_result_075_15.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()