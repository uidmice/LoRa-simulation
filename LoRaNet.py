import random
import math
import sys
import re
import os
import operator

import simpy
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from Node import *


if len(sys.argv) >= 4:
    avgSendTime = int(sys.argv[1])
    full_collision = int(sys.argv[2])
    Rnd = random.seed(int(sys.argv[3]))
    print ("AvgSendTime (exp. distributed):",avgSendTime)
    print ("Full Collision: ", full_collision)
    print ("Random Seed: ", int(sys.argv[3]))
else:
    print ("usage: ./confirmablelorawan <avgsend> <collision> <randomseed>")
    exit(-1)


nodes = []
packetsAtBS = []
bs = BaseStation(1, 0, 0)
env = simpy.Environment()


n_loc = np.loadtxt('deployment.dat')
for i in range(len(n_loc)):
    node = myNode(i,avgSendTime, n_loc[i,0], n_loc[i,1])
    nodes.append(node)
