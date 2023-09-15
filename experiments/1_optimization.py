#!/usr/bin/env python

from statistics import mean 
import pandas as pd

import sys
import csv

import sys 
import os
path = os.path.dirname(os.getcwd())
sys.path.append(path)
from lib import *

path = os.path.dirname(os.getcwd())



data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../xml_parser/flightBooking.json')

df = pd.read_csv(r'../data/DE_2020.csv')
ci_data = df['carbon_intensity_avg']

df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021 = df['carbon_intensity_avg']

df = pd.read_csv(r'../data/projectcount_wikiDE_2014.csv')
clickData_hourly_2014 = df["de"]
carbonBudget = calcCarbonBudgetHourInWeekAVG(2020,clickData_hourly_2014,ci_data)

year=2015
weekday_frequency = weekdayfrequency(year)
s = weekday_frequency.index(53)*24


weekday_frequency = weekdayfrequency(2021)
s_2021 = weekday_frequency.index(53)*24


indices = []
for ms in data['components']:
    indices.append([0] * len(data['components'][ms]))

df = pd.read_csv(r'../data/projectcount_wikiDE_2015.csv')
clickData_hourly = df["De"].tolist()
clickData_hourly = clickData_hourly[24:] + clickData_hourly[0:24]

row = ["q","user-throughput","ed","eb","U","ce"]
f = open('../results/optimization_result.csv', 'w')
writer = csv.writer(f)
writer.writerow(row)
f.close()


for t in range(len(ci_data_2021)):
    index = (t+s_2021)%168
    eb = carbonBudget[index]/ci_data_2021[t]
    qValue,userThrougput,ed = optimizationHourly(eb, clickData_hourly[t], indices, userMax, energyDemand, q)
    ce = ed * ci_data_2021[t]
    row = [qValue,userThrougput,ed,eb,clickData_hourly[t],ce]
    f = open('../results/optimization_result.csv', 'a')
    writer = csv.writer(f)
    writer.writerow(row)
    f.close()