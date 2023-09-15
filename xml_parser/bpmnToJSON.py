
# Can use BeautifulSoup to parse XML
# from bs4 import BeautifulSoup

# Or use Elementtree

import xml.dom.minidom
import json
import sys


def importXML(fileName):
    return(xml.dom.minidom.parse(fileName))

bpmn = importXML(sys.argv[1])


## Read from BPMN
participant = bpmn.getElementsByTagName("bpmn:participant")
for i in participant:
    name = i.getAttribute("name")

serviceTask = bpmn.getElementsByTagName("bpmn:serviceTask")
ms = []
for i in serviceTask :
    ms.append(i.getAttribute("name"))
ms_iterator = [s.replace("\n", " ") for s in ms]
ms = list(ms_iterator)

# Execution Formats
ms_name = []
for i in ms:
    if i.find("[") != -1:
        s = i.find("[")
        t = i.find("]")
        i = i.replace(i[s:t+1], "")
    ms_name.append(i)
ms_name = list(dict.fromkeys(ms_name))

execution_formats = [[] for x in range(len(ms_name))]
for i in ms:
    if i.find("[") != -1:
        s = i.find("[")
        t = i.find("]")
        temp_indexFinder = i.replace(i[s:t+1], "")
        ms_iter = ms_name.index(temp_indexFinder)
        print(ms_iter)
        execution_formats[ms_iter].append(i[s+1:t])
    else:
        temp_indexFinder = i
        ms_iter = ms_name.index(temp_indexFinder)
        execution_formats[ms_iter].append("")

## Write to JSON
jsObj = {
    "name": name,
    "components": {

    }
}
for i in ms_name:
    jsObj["components"][i] = {
    }
    for j in execution_formats[ms_name.index(i)]:
        jsObj["components"][i][j] = {
                "aws-ec2-type": "",
                "energy-demand": 0.0,
                "user-scaling": 0,
                "q": 0.0
        }
json_object = json.dumps(jsObj, indent = 4)
# Write to json
with open(name + ".json", "w") as outfile:
    outfile.write(json_object)