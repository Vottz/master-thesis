import requests
import json
from datetime import *
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import csv
import pandas as pd

import gurobi as gb
from gurobipy import GRB


import math
from statistics import mean 

import subprocess

import sys 
import os

from lib import *
path = os.getcwd()

# Selective Optimisation Algorithm 
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

    # Variables
    b = m.addVars(shape, vtype=GRB.BINARY, name="b")
    u = m.addVars(len(indices)+1, lb=0.0, vtype=GRB.CONTINUOUS, name="u") # ub=20.0 ?

    # Scaling Factor. Indicates how many instances are needed to serve the user demand. For each microservice
    sf = m.addVars(shape, lb=0, vtype=GRB.INTEGER, name="sf")
    m.update()
    # ToDo: Ensure that mandatory/core microservices always have one execution format running
        
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


    # Extract Output
    qValue = [var.X for var in m.getVars() if "u" in var.VarName][5]
    userThrougput = [var.X for var in m.getVars() if "u" in var.VarName][5] * user_demand
    ed = 0
    execFormats = [var.X for var in m.getVars() if "b" in var.VarName]
    scalingFactor = [var.X for var in m.getVars() if "sf" in var.VarName]
    energyDemand_flat = [item for sublist in energyDemand for item in sublist]
    for i in range(len(execFormats)):
        ed += execFormats[i]*scalingFactor[i]*energyDemand_flat[i]
    return(qValue,userThrougput,ed)

# Helper Functions

#https://stackoverflow.com/questions/43692340/how-to-find-number-of-mondays-or-any-other-weekday-between-two-dates-in-python
def num_days_between(start, end, week_day):
    """
    Calculates the number of times a weekday occurs between two dates

    :param p1: start date
    :param p2: end date
    :param p3: day of the week (0 = Monday,...,6 = Sunday)
    :return: number of times p3 occurs between p1 and p2
    """ 
    num_weeks, remainder = divmod((end-start).days, 7)
    if ( week_day - start.weekday() ) % 7 < remainder:
       return num_weeks + 1
    else:
       return num_weeks

def weekdayfrequency(year):
    """
    Calculates the frequency of each weekday in a given year

    :param p1: year
    return: list of the frequency each weekday occurs in that year
    """
    return([num_days_between(date(year, 1, 1), date(year+1, 1, 1), i) for i in range(7)])


# Data Import functions
## 1.  Get BPMN data constants
def getConstantsFromBPMN(bpmnFile):
    """
    Extracts the constants from a given JSON file

    :param p1: bpmnFile [in JSON]
    return: data, vars_ms, userMax, energyDemand, q
    """
    with open(bpmnFile) as data_file:
        data = json.load(data_file)
        vars_ms = [[]] * len(data['components'])
        userMax = []
        energyDemand = []
        q = []
        i = 0 
        for ms in data['components']:
            ca = data['components'][ms]
            vars_ms[i].append(ms)
            j = 1
            userMax.append([])
            energyDemand.append([])
            q.append([])
            for x in ca.items():
                if type(x) == str:
                    j += 1
                else:
                    vars_ms[i].append(x)
                    if x[1]["user-scaling"] is None:
                        userMax[i].append(10000000000) # ToDo: Fix this workaround. set to 10000000000?
                    else:
                        userMax[i].append(x[1]["user-scaling"])
                    energyDemand[i].append(x[1]["energy-demand"])
                    q[i].append(x[1]["q"])
                    #ms_j_q = j["q"]
                    j += 1
            i += 1
            #ms = m.addVars(vars_ms, name="ms") #Has to be splitted into multiple variables: 'energy-demand', 'user-scaling', 'q'
            # multidict(vars_ms)
    return(data, vars_ms, userMax, energyDemand, q)


## 2. Energy Budget

### a) Energy Demand depending on user data
def calcEnergyDemandFromAVG(clickData_hourly):
    """
    Calculates the Energy Demand of the average architecture for a given user request dataset

    :param p1: user request Data
    return: Energy Demand per Hour
    """
    data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')
    # AVG deployment data

    ## AVG q per ms in Architecture
    avgQ = [mean(q[i]) for i in range(len(q))]

    ## AVG user-max per ms in Architecture
    avg_userMax = [mean(userMax[i]) for i in range(len(q))]

    ## AVG Users per Microservice
    user_avg = [[] for x in range(8760)]
    for i in range(8760):
        user_avg[i].append(clickData_hourly[i])
        user_avg[i].append(clickData_hourly[i] * avgQ[0])
        for j in range(1,len(avgQ)):
            user_avg[i].append(user_avg[i][j] * avgQ[j])

    ## and number of machines needed per microservice (Scaling Factor)
    avg_numInstances = [[] for x in range(8760)]
    for i in range(8760):
        for j in range(len(userMax)):
            temp = user_avg[i][j] / avg_userMax[j]
            if math.isnan(temp):
                avg_numInstances[i].append(0)
                print(temp,i)
            else:
                avg_numInstances[i].append(math.ceil(user_avg[i][j] / avg_userMax[j]))
    ## AVG ED per ms in Architecture
    avgEnergyDemand = [mean(energyDemand[i]) for i in range(len(energyDemand))]
    ## SF of AVG deployment
    ed = [[] for x in range(8760)] # in kwH per microservice per hour
    for i in range (0, 8760):
        ed[i] = [avgEnergyDemand[j] * avg_numInstances[i][j] for j in range(len(avgEnergyDemand))]
    return(ed)

def calcQFromAVG(clickData_hourly):
    """
    Calculates the Revenue of the average architecture for a given user request dataset

    :param p1: user request Data
    return: Energy Demand per Hour
    """

    data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')

    ## AVG q per ms in Architecture
    avgQ = [mean(q[i]) for i in range(len(q))]

    ## AVG user-max per ms in Architecture
    avg_userMax = [mean(userMax[i]) for i in range(len(q))]

    ## AVG Users per Microservice
    user_avg = [[] for x in range(8760)]
    for i in range(8760):
        user_avg[i].append(clickData_hourly[i])
        user_avg[i].append(clickData_hourly[i] * avgQ[0])
        for j in range(1,len(avgQ)):
            user_avg[i].append(user_avg[i][j] * avgQ[j])

    ## and number of machines needed per microservice (Scaling Factor)
    avg_numInstances = [[] for x in range(8760)]
    for i in range(8760):
        for j in range(len(userMax)):
            temp = user_avg[i][j] / avg_userMax[j]
            if math.isnan(temp):
                avg_numInstances[i].append(0)
                print(temp,i)
            else:
                avg_numInstances[i].append(math.ceil(user_avg[i][j] / avg_userMax[j]))
    ## AVG ED per ms in Architecture
    avgEnergyDemand = [mean(energyDemand[i]) for i in range(len(energyDemand))]
    ## SF of AVG deployment
    ed = [[] for x in range(8760)] # in kwH per microservice per hour
    for i in range (0, 8760):
        ed[i] = [avgEnergyDemand[j] * avg_numInstances[i][j] for j in range(len(avgEnergyDemand))]
    return(user_avg)


def calcCarbonEmissionFromEnergyDemand(ed, ci_data):
    """
    Calculates the carbon emissions for a given energy demand and carbon intensity data

    :param p1: energy demand per hour [kWh]
    :param p2: carbon intensity data per hour [gCO2eq per kWh]

    return: carbon emissions per hour
    """
    data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')

    if len(ci_data) > 8760:
        ci_list = ci_data.tolist()
        ci_data = ci_list[0:1416] + ci_list[1416+24:8784]

    emissionsPerHour = []
    for i in range(8760):
        emissionsPerHour.append(sum(ed[i][j] * ci_data[i] for j in range(len(energyDemand))))
    return(emissionsPerHour)

def calcCarbonBudgetFrom_AVG_CE(clickData_hourly,ci_data):
    """
    Calculates the annual carbon budget for a given user request dataset and carbon intensity data

    :param p1: clickData_hourly: user request data for a given year [int]
    :param p2: ci_data: carbon intensity data for a given year [gCO2eq per kWh]

    return: carbon budget for a given year [gCO2eq]
    """
    # ToDo: Think how to handle 2020 and 2015 user data set, because 2015 is not a leap year
    avgCE = sum(calcCarbonEmissionFromEnergyDemand(calcEnergyDemandFromAVG(clickData_hourly),ci_data))
    cb = avgCE*0.923
    return(cb)


def calcCarbonBudget_hourly(clickData_hourly):
    """
    Calculates the mean carbon budget per hour in week for a given user request dataset

    :param p1: clickData_hourly: user request data for a given year [int]

    return: carbon budget for a given year [gCO2eq]
    """
    # 2020 had 8784 hours (Leap year)
    # ToDo: Think how to handle 2020 and 2015 user data set, because 2015 is not a leap year
    cb = calcCarbonBudgetFrom_AVG_CE(clickData_hourly)
    cbPerHour = cb / 8760
    return(cbPerHour) # in gCO2eq

### b) Weekly Time Series Budget Calculation
def getS_hourlyAVG(clickData_hourly, year):
    """
    Calculates the hourly average of user request in hour in week for a given year with its user-request data

    :param p1: clickData_hourly: user request data for a given year
    :param p2: year: year of calculation

    return: hourly average of user request in hour in week for a given year
    """
    weekday_frequency = weekdayfrequency(year)
    s_hourly = [0] * 168
    for i in range(len(clickData_hourly)):
        hourInWeek = (i+72) % 168
        s_hourly[hourInWeek] += clickData_hourly[i]
    s_hourlyAVG = [0] * 168
    for i in range(7):
        for j in range(24):
            index = (i*24)+j
            s_hourlyAVG[index] = s_hourly[index] / weekday_frequency[i]
    return(s_hourlyAVG)

def calcCarbonBudgetHourInWeekAVG(year, clickData_hourly, ci_data):
    '''
    Calculates the mean carbon budget per hour in a week for a given year

    :param p1:    year of calculation, int
    :param p2:    user request data for that year, [int] size is 8760 or 8784 in leap years
    :param p3:    CI data for that year ,[int] size is 8760 or 8784 in leap years

    return: The mean carbon budget per hour in a week for the given year
    '''
    s_hourlyAVG = getS_hourlyAVG(clickData_hourly, year)
    weekday_frequency = weekdayfrequency(year)
    # s = weekday_frequency.index(53)*24
    
    user_total_annually = sum(clickData_hourly)
    carbonEmission = calcCarbonEmissionFromEnergyDemand(calcEnergyDemandFromAVG(clickData_hourly),ci_data)
    carbonEmission = sum(carbonEmission)

    carbonBudget_anually = carbonEmission * 0.923
    cb_perUser = carbonBudget_anually / user_total_annually
    cb_perHour = [s_hourlyAVG[i] * cb_perUser for i in range(len(s_hourlyAVG))]

    # # Because the cb_perHour is static, we can adjust it with the CI for 2021
    # carbonBudget = [0 for i in range(168)]
    # for t in range(len(ci_data)):
    #     index = (t+s) % 168
    #     carbonBudget[index] += cb_perHour[index]
    # for i in range(168):
    #     carbonBudget[i] = carbonBudget[i] / weekday_frequency[i%7]
    return(cb_perHour)


def calcED_LP(userMax, energyDemand, q, clickData):
    '''
    Calculates the energy demand for the low power architecture

    :param p1: userMax
    :param p2: energyDemand
    :param p3: q
    :param p4: clickData

    return: qValue,clickData,ed
    '''
    ed = 0
    for j in range(len(q)):
        if userMax[j][0] > 0:
            ed += energyDemand[j][0] * math.ceil(clickData / userMax[j][0])
        clickData = clickData * q[j][0]
    qValue = math.prod([q[i][0] for i in range(len(q))])
    return(qValue,clickData,ed)