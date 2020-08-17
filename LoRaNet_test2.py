import random
import math
import sys
import re
import os
import operator

import simpy
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from Node import Node, EnergyProfile
from Gateway import Gateway, DownlinkPacket
from TransmissionInterface import AirInterface
from LoRaParameters import LoRaParameters
from External import RandomExternal
from Server import Server
from config import *

if len(sys.argv) >= 4:
    x = int(sys.argv[1])
    sim_time = int(sys.argv[2])
    mode = int(sys.argv[3])
    print ("Simulation time:",sim_time)
else:
    print ("usage: ./LoRaNet <num_nodes> <sim_time/min> ")
    exit(-1)


nodes = []
gateways = []



# n_loc = np.loadtxt('deployment.dat')
# x_min = np.min(n_loc[:,0])
# x_max = np.max(n_loc[:,0])
# y_min = np.min(n_loc[:,1])
# y_max = np.max(n_loc[:,1])

# for i in range(len(n_loc)):
#     node = Node(i, EnergyProfile(3.3), LoRaParameters(i%Gateway.NO_CHANNELS, sf = i%Gateway.NO_CHANNELS+7), n_loc[i,0],
#      n_loc[i,1],gateways, 10, air, sim_env )
#     nodes.append(node)
#     sim_env.process(node.run()) #10% chance of sending a packet





# input('Press Enter to continue ...')

sim_env = simpy.Environment()
air = AirInterface(sim_env)
gateways.append(Gateway(0, 0, 0,  sim_env))
server = Server(mode = mode)
node = Node(0, EnergyProfile(3.3), LoRaParameters(0, sf = 10), x,
              0,gateways, 5, server, air, sim_env)
nodes.append(node)
sim_env.process(node.run())
sim_env.run(sim_time*MINUTE_TO_MS)

received = [x.num_unique_packets_sent for x in nodes]
sent = [x.num_packets_sent for x in nodes]

print("Numbers of packets sent (including retransmission):")
print(sent)
print("Numbers of packets successfully received:")
print(received)
