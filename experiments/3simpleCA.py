#!/usr/bin/env python
from datetime import *
import csv
import pandas as pd

import math
from statistics import mean 
import sys 
import os

path = os.path.dirname(os.getcwd())
sys.path.append(os.path.abspath(path))
from lib import *

# Application Architecture Data
data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')
# User Data
df = pd.read_csv(r'../data/projectcount_wikiDE_2014.csv')
clickData_hourly_2014 = df["de"]
# CI Data
df = pd.read_csv(r'../data/DE_2020.csv')
ci_data = df['carbon_intensity_avg']


carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)

# Defining 3 execution formats
# q, energyDemand, user_max
lowPower = []
normalPower = []
highPower = []
for i in range(len(vars_ms)):
    lowPower.append([q[i][0],energyDemand[i][0],userMax[i][0]])
    normalPower.append([q[i][-1],energyDemand[i][-1],userMax[i][-1]])
    highPower.append([q[i][-1],energyDemand[i][-1],userMax[i][-1]])

lowPower[1] = [0.9,0,10000000000]
lowPower[4] = [0.75,0,10000000000]

normalPower[0] = [0.7,39.9,12000]
normalPower[1] = [0.9,0,10000000000]
normalPower[4] = [0.9,39.9,12000]

def energyDemand(configuration, user_demand):
    ed = math.ceil(user_demand / configuration[0][2]) * configuration[0][1]
    user_temp = user_demand * configuration[0][0]
    for i in range(1,len(configuration)):
        if (configuration[i][2] == 10000000000): #ToDo find a better way
            ed += 0
        else:
            ed += math.ceil(user_temp / configuration[i][2]) * configuration[i][1]
        user_temp *= configuration[i][0]
    return(ed)

df = pd.read_csv(r'../data/projectcount_wikiDE_2015.csv')
clickData_hourly = df["De"].tolist()
clickData_hourly = clickData_hourly[24:] + clickData_hourly[0:24]

df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021 = df['carbon_intensity_avg']


weekday_frequency = weekdayfrequency(2021)
s = weekday_frequency.index(53)*24


row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/3_simpleCA_result.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()


for t in range(8760):
    index = (t+s) % 168
    #eb_temp  = cb_perHour[index] / ci_data_2021_hourly[i]    
    ed = 0
    ed_hp = energyDemand(highPower, clickData_hourly[t])
    ed_np = energyDemand(normalPower, clickData_hourly[t])
    eb = carbonBudget[index]/ci_data_2021[t]
    
    if ed_hp <= eb:
        ed = ed_hp
        q = math.prod([highPower[j][0] for j in range(len(vars_ms))])
        row = [q,q*clickData_hourly[t],ed]
    elif ed_np <= eb:
        ed = ed_np
        q = math.prod([normalPower[j][0] for j in range(len(vars_ms))])
        row = [q,q*clickData_hourly[t],ed]
    else:
        ed = energyDemand(lowPower, clickData_hourly[t])
        q = math.prod([lowPower[j][0] for j in range(len(vars_ms))])
        row = [q,q*clickData_hourly[t],ed]
    # Writing results to CSV
    f = open('../results/3_simpleCA_result.csv', 'a')
    row.append(eb)
    row.append(clickData_hourly[t])
    row.append(ed * ci_data_2021[t])
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()
    if t%168 == 0:
        eb = [0]*168
        for i in range(len(carbonBudget)):
            index2 = (i+s)%168
            eb[index2] = carbonBudget[index2]/ci_data_2021[t+i]
            if t+i == len(clickData_hourly)-1:
                break