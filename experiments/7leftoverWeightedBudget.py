#!/usr/bin/env python
"""
Hourly Optimizer for a full year
with energy budget recycl. 
Weighted redistribution.


Returns: Energy demand for every hour 
"""
from statistics import mean 
import pandas as pd

import sys
import csv

import sys 
import os
path = os.path.dirname(os.getcwd())
sys.path.append(path)
from lib import *



def recalcCB(carbonBudget, leftoverCB):
    carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)
    for i in range(168):
        carbonBudget[i] += leftoverCB[i]
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

row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/7_leftoverWeighted_optimization_result.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()

weekday_frequency = weekdayfrequency(2021)
s_2021 = weekday_frequency.index(53)*24

carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)
cb = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data) # for recalculation
leftOver = [0] * 168
for t in range(0,len(clickData_hourly)):
    index = (t+s_2021)%168
    if index == 0 and t != 0:
        carbonBudget = recalcCB(cb, leftOver)
        leftOver = [0] * 168
    eb = carbonBudget[index]/ci_data_2021[t]
    qValue,userThrougput,ed = optimizationHourly(eb, clickData_hourly[t], indices, userMax, energyDemand, q)
    ce = ed * ci_data_2021_hourly[t]
    row = [qValue,userThrougput,ed,eb,clickData_hourly[t],ce]
    f = open('../results/7_leftoverWeighted_optimization_result.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()
    leftOver[index] = carbonBudget[index] - ce