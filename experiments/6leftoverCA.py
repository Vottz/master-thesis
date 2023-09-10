#!/usr/bin/env python
"""
Selective Optimizer for a full year


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

# Command-Line Arguments
#cliArg = sys.argv[1:]
#energyBudget = float(cliArg[0])
#userDemand = float(cliArg[1])



def recalcCB(leftoverCB):
    carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)
    extraBudget = leftoverCB / 168
    for i in range(168):
        carbonBudget[i] += extraBudget
    return(carbonBudget)

# Parameters Import
data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')
indices = []
for ms in data['components']:
    indices.append([0] * len(data['components'][ms]))

df = pd.read_csv(r'../data/projectcount_wikiDE_2015.csv')
clickData_hourly = df["De"].tolist()
clickData_hourly = clickData_hourly[24:] + clickData_hourly[0:24]

df = pd.read_csv(r'../data/DE_2020.csv')
ci_data = df['carbon_intensity_avg']

df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021 = df['carbon_intensity_avg']

df = pd.read_csv(r'../data/projectcount_wikiDE_2014.csv')
clickData_hourly_2014 = df["de"]

df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021_hourly = df['carbon_intensity_avg']


weekday_frequency = weekdayfrequency(2021)
s_2021 = weekday_frequency.index(53)*24

row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/6_leftover_optimization_result.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()

carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)
leftOver = 0
for t in range(0,len(clickData_hourly)):
    index = (t+s_2021)%168
    if index == 0 and t != 0:
        carbonBudget = recalcCB(leftOver)
        leftOver = 0
    eb = carbonBudget[index]/ci_data_2021[t]
    qValue,userThrougput,ed = optimizationHourly(eb, clickData_hourly[t], indices, userMax, energyDemand, q)
    ce = ed * ci_data_2021_hourly[t]
    row = [qValue,userThrougput,ed,eb,clickData_hourly[t],ce]
    f = open('../results/6_leftover_optimization_result.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()
    leftOver += carbonBudget[index] - ce
    if leftOver < 0:
        leftOver = 0