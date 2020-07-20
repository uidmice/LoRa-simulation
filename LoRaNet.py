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
from config import *

if len(sys.argv) >= 3:
    num_nodes = int(sys.argv[1])
    sim_time = int(sys.argv[2])
    print ("Number of nodes:",num_nodes)
    print ("Simulation time:",sim_time)
else:
    print ("usage: ./LoRaNet <num_nodes> <sim_time/min> ")
    exit(-1)


nodes = []
packetsAtBS = []
gateways = []
sim_env = simpy.Environment()
air = AirInterface(sim_env)
gateways.append(Gateway(0, 0, 0,  sim_env))


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

plt.ion()
plt.figure()
plt.xlim([-MAX_DISTANCE, MAX_DISTANCE])
plt.ylim([-MAX_DISTANCE, MAX_DISTANCE])
ax = plt.gcf().gca()
ax.add_artist(plt.Circle((0, 0), GRID, fill=False, color='green'))

for i in range(num_nodes):
    x = np.random.randint(-CORD, CORD) * GRID
    y = np.random.randint(-CORD, CORD) * GRID
    node = Node(i, EnergyProfile(3.3), LoRaParameters(i%Gateway.NO_CHANNELS, sf = 12), x,
          y,gateways, 20, air, sim_env )
    # node = Node(i, EnergyProfile(3.3), LoRaParameters(0, sf = 12), x, y,gateways, 20, air, sim_env )
    nodes.append(node)
    ax.add_artist(plt.Circle((x, y), GRID/2, fill=True, color='blue'))
    sim_env.process(node.run())
    plt.draw()
    plt.pause(0.001)
    plt.show()
sim_env.run(sim_time*60000)

received = [x.num_unique_packets_sent for x in nodes]
sent = [x.num_packets_sent for x in nodes]

print('Of ', num_nodes, " nodes:")
print("Numbers of packets sent (including retransmission):")
print(sent)
print("Numbers of packets successfully received:")
print(received)
print('')
tol_sent = sum(sent)
tol_receive = sum(received)
print("Total number of packets sent: ", tol_sent)
print("Total number of packets successfully received: ", tol_receive)
print("Success ratio: {:.2f}%".format( tol_receive*1.0/tol_sent*100))


input('Press Enter to continue ...')
