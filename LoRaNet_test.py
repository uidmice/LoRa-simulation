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
from External import *
from config import *



nodes = []
gateways = []

num_runs = 3
nums_nodes = range(0,300,10)
ch_usage = np.zeros((num_runs, len(nums_nodes)))
throughput = np.zeros((num_runs, len(nums_nodes)))

for k in range(num_runs):
    for j in range(len(nums_nodes)):
        print("========new test=========")
        num_nodes = nums_nodes[j]
        sim_env = simpy.Environment()
        air = AirInterface(sim_env)
        gateways.append(Gateway(0, 0, 0,  sim_env))
        for i in range(num_nodes):
            x = np.random.randint(-CORD, CORD+1) * GRID
            y = np.random.randint(-CORD, CORD+1) * GRID
            node = Node(i, EnergyProfile(3.3), LoRaParameters(0, sf = 10), x,
                  y,gateways, 5, air, sim_env)
            nodes.append(node)
            sim_env.process(node.run())
        print("#nodes in the list = {}".format(len(nodes)))
        sim_env.run(3*MINUTE_TO_MS)
        received = [x.num_unique_packets_sent for x in nodes]
        sent = [x.unique_packet_id for x in nodes]
        tol_sent = sum(sent)
        tol_receive = sum(received)
        print("Total packet sent = {}".format(tol_sent))
        print("Total packet receive = {}".format(tol_receive))
        ch_usage[k, j] = tol_sent
        throughput[k, j] = tol_receive
        nodes = []
        gateways = []

print(repr(ch_usage))
print(repr(throughput))
plt.plot(ch_usage, throughput)
plt.show()
