#!/usr/bin/env python
"""
Hourly Optimizer for a full year


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
import random as rd

# Command-Line Arguments
#cliArg = sys.argv[1:]
#energyBudget = float(cliArg[0])
#userDemand = float(cliArg[1])


def randomEB(hourly_eb):
    n = rd.uniform(0.8,1.2)
    return (hourly_eb * float(str(n)[:5]))



row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/9_randomEB_optimization_08_12.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()


data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')
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
    eb_sum,qValue_sum,userThrougput_sum,ed_sum,ce = 0,0,0,0,0
    index = (t+s)%168
    for i in range(10):
        eb = randomEB(carbonBudget[index]/ci_data_2021[t])
        qValue,userThrougput,ed = calcED_LP(userMax, energyDemand, q, clickData_hourly[t])
        if ed < eb:
            qValue,userThrougput,ed = optimizationHourly(eb, clickData_hourly[t], indices, userMax, energyDemand, q)
        ce += ed * ci_data_2021[t]
        eb_sum += eb
        qValue_sum += qValue
        userThrougput_sum += userThrougput
        ed_sum += ed
    result = [qValue_sum,userThrougput_sum,ed_sum,eb_sum,clickData_hourly[t],ce]
    row = [x/10 for x in result]
    f = open('../results/9_randomEB_optimization_08_12.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()