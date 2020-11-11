

import simpy
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap
import numpy as np
from scipy.stats import norm

from framework.Node import Node, EnergyProfile
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface
from framework.LoRaParameters import LoRaParameters
from framework.External import *
from framework.Server import Server
from config import *



nodes = []
gateways = []

sim_time = 2
plt.ion()
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(1,1,1)

sim_env = simpy.Environment()
air = AirInterface(sim_env)
external = TempExternal(sim_env)
gateways.append(Gateway(0, 0, 0,  sim_env))
server = Server()
im = ax.imshow(external.T, alpha=.5, interpolation='bicubic', cmap='RdYlGn_r', origin='lower'
,extent=[-MAX_DISTANCE, MAX_DISTANCE, - MAX_DISTANCE, MAX_DISTANCE]
)
ax.axes.xaxis.set_visible(False)
ax.axes.yaxis.set_visible(False)
plt.colorbar(im, cmap='hot')
im.set_clim(80, 20)
plt.axis('off')
plt.draw()
plt.show()

newax = fig.add_axes(ax.get_position(), frameon=False)
newax.add_artist(plt.Circle((0, 0), GRID, fill=False, color='green'))
newax.set_xlim([-MAX_DISTANCE, MAX_DISTANCE])
newax.set_ylim([-MAX_DISTANCE, MAX_DISTANCE])

contour_ax = fig.add_axes(newax.get_position(), frameon=False)
contour_ax.set_xlim([-MAX_DISTANCE, MAX_DISTANCE])
contour_ax.set_ylim([-MAX_DISTANCE, MAX_DISTANCE])
# input('Press Enter to continue ...')
n_id = 0
num_nodes = len(range(-CORD+5,CORD+1,10))**2
transmission_status = np.zeros(num_nodes)
patches = []
for i in range(-CORD+5,CORD+1,10):
    for j in range(-CORD+5,CORD+1,10):
        x = j * GRID
        y = i * GRID
        patches.append(Circle((x, y),  GRID, fill=True))
        node = Node(n_id, EnergyProfile(3.3), LoRaParameters(i%Gateway.NO_CHANNELS, sf = 12), x,
              y,gateways, 20, server, air, sim_env , external = external, status = transmission_status)
        nodes.append(node)
        n_id += 1
        sim_env.process(node.run())

cmap = ListedColormap([ "red", "black","blue"])
p = PatchCollection(patches, cmap=cmap)
p.set_clim([-1, 1])
newax.add_collection(p)

class Status:

    def __init__(self):

        self.transmission = transmission_status
        self.patches = p

def status_update():
    while True:
        p.set_array(transmission_status)
        plt.draw()
        plt.pause(0.0001)
        plt.show()
        yield sim_env.timeout(10)

sim_env.process(external.update(im, contour_ax, Status()))
sim_env.run(sim_time*MINUTE_TO_MS)

received = [x.num_unique_packets_sent for x in nodes]
sent = [x.num_packets_sent for x in nodes]
time = [x.transmit_time for x in nodes]
energy_usage = [x.energy_profile.origin_E_tot - x.energy_profile.E_tot for x in nodes]

num_nodes = len(nodes)
print('Of ', num_nodes, " nodes:")
print("Numbers of packets sent (including retransmission):")
print(sent)
print("Numbers of packets successfully received:")
print(received)
print("Total transmission time: (s)")
print(np.array(time)/1000.0)
print("Total energy consumption: (J)")
print(np.array(energy_usage)/1000.0)
print('')
tol_sent = sum(sent)
tol_receive = sum(received)
ave_e = np.average(energy_usage)
max_e = np.max(energy_usage)
print("Total number of packets sent: ", tol_sent)
print("Total number of packets successfully received: ", tol_receive)
print("Average duty circle: ", np.average(time)/(sim_time*MINUTE_TO_MS)*100, "%")
print("Average energy consumption: {:.2f}(mJ), {:.2f}% ".format(ave_e, ave_e/BATTERY_ENERGY*100) )
print("Maximum energy consumption: {:.2f}(mJ), {:.2f}%".format(max_e, max_e/BATTERY_ENERGY*100))
print("Success ratio: {:.2f}%".format( tol_receive*1.0/tol_sent*100))


input('Press Enter to continue ...')
