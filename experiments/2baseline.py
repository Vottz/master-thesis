#!/usr/bin/env python
from datetime import *
from statistics import mean 
from itertools import product
import sys 
import os
path = os.path.dirname(os.getcwd())
sys.path.append(path)
from lib import *

data, vars_ms, userMax, energyDemand, q = getConstantsFromBPMN('../flightBooking.json')
# User Data
df = pd.read_csv(r'../data/projectcount_wikiDE_2015.csv')
clickData_hourly = df["De"].tolist()
clickData_hourly = clickData_hourly[24:] + clickData_hourly[0:24]

# Low Power
ed_hourly_lowPower = []
prodQ = 1.0
for i in range(8760):
    ed = 0
    s = clickData_hourly[i]
    for j in range(len(q)):
        if userMax[j][0] > 0:
            ed += energyDemand[j][0] * math.ceil(s / userMax[j][0])
        s = s * q[j][0]

    ed_hourly_lowPower.append(ed)


# Normal 
lowPower_ed = sum(energyDemand[i][0] for i in range(len(energyDemand)))
highPower_ed = sum(energyDemand[i][-1] for i in range(len(energyDemand)))

median_ed = (highPower_ed - lowPower_ed)/2


indices = []
for ms in data['components']:
    indices.append([0] * len(data['components'][ms]))

# Calculating all possible configurations
vars_gb = [[]]
for i in indices:
    vars_gb *= len(i)
ed_combo = list(product(*energyDemand))
userMax_combo = list(product(*userMax))
q_combo = list(product(*q))

for i in range(len(vars_gb)):
    vars_gb[i].append([ed_combo[i], userMax_combo[i], q_combo[i]])
# Finding the configuration with the closest energy demand to the median energy demand
temp = highPower_ed
for i in range(len(vars_gb)):
    if abs(sum(vars_gb[0][i][0])-median_ed) < temp:
        temp = abs(sum(vars_gb[0][i][0])-median_ed)
        index = i
normal_conf = vars_gb[0][index]
ed_hourly_normal = []
for i in range(8760):
    ed = 0
    s = clickData_hourly[i]
    for j in range(len(q)):
        if normal_conf[1][j] > 0:
            ed += normal_conf[0][j] * math.ceil(s / userMax[j][0])
        s = s * normal_conf[2][j]
    ed_hourly_normal.append(ed)

# High Performance
ed_hourly_highPower = []
for i in range(8760):
    ed = 0
    s = clickData_hourly[i]
    for j in range(len(q)):
        if userMax[j][-1] > 0:
            ed += energyDemand[j][-1] * math.ceil(s / userMax[j][-1])
        s = s * q[j][-1]
    ed_hourly_highPower.append(ed)


df = pd.read_csv(r'../data/DE_2021.csv')
ci_data_2021_hourly = df['carbon_intensity_avg']

ed_daily_highPower = []
for i in range(365):
    temp = 0
    for j in range(24):
        temp += ed_hourly_highPower[i*24+j]*ci_data_2021_hourly[i*24+j]
    ed_daily_highPower.append(temp)

ed_hourly_lowPower = np.array(ed_hourly_lowPower)
#ed_hourly_highPower[1000] = 6277312.0
#ed_hourly_highPower[1001] = 6277312.0
ed_hourly_highPower = np.array(ed_hourly_highPower)

data = pd.DataFrame({'lp': ed_hourly_lowPower, 'hp': ed_hourly_highPower}, columns=['lp', 'hp'])

# Write to CSV
f = open('../results/2_baseline.csv', 'w')
writer = csv.writer(f)
row = ["lp","np","hp"]
writer.writerow(row)
for lp,np,hp in zip(ed_hourly_lowPower,ed_hourly_normal,ed_hourly_highPower):
    row = []
    row.append(lp)
    row.append(np)
    row.append(hp)
    writer.writerow(row)
f.close()