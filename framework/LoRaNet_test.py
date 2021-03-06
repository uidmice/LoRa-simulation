

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
from framework.Environment import *
from framework.Backend import Server
from config import *



nodes = []
gateways = []

sim_time = 2
plt.ion()
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(1,1,1)

sim_env = simpy.Environment()
air = AirInterface(sim_env)
external = TempEnvironment(sim_env)
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

