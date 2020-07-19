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

from Node import Node, EnergyProfile
from Gateway import Gateway, DownlinkPacket
from TransmissionInterface import AirInterface
from LoRaParameters import LoRaParameters
from config import *

# if len(sys.argv) >= 4:
#     avgSendTime = int(sys.argv[1])
#     full_collision = int(sys.argv[2])
#     Rnd = random.seed(int(sys.argv[3]))
#     print ("AvgSendTime (exp. distributed):",avgSendTime)
#     print ("Full Collision: ", full_collision)
#     print ("Random Seed: ", int(sys.argv[3]))
# else:
#     print ("usage: ./confirmablelorawan <avgsend> <collision> <randomseed>")
#     exit(-1)


nodes = []
packetsAtBS = []
gateways = []
sim_env = simpy.Environment()
air = AirInterface()

if (graphics == 1):
    plt.ion()
    plt.figure()
    ax = plt.gcf().gca()
    ax.add_artist(plt.Circle((0, 0), 3, fill=True, color='green'))

gateways.append(Gateway(0, 0, 0,  sim_env))

n_loc = np.loadtxt('deployment.dat')
for i in range(len(n_loc)):
    node = Node(i, EnergyProfile(3.3), LoRaParameters(i%Gateway.NO_CHANNELS, sf = i%Gateway.NO_CHANNELS+7), n_loc[i,0],
     n_loc[i,1],gateways, 10, air, sim_env )
    nodes.append(node)
    sim_env.process(node.run()) #10% chance of sending a packet
    if (graphics == 1):
        ax.add_artist(plt.Circle((node.x, node.y), 2, fill=True, color='blue'))

if (graphics == 1):
    plt.draw()
    plt.show()

sim_env.run()
