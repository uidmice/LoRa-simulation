from framework.Node import *
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface, Location
from framework.Server import Server, Application
from framework.LoRaParameters import LoRaParameters
from framework.Environment import TempEnvironment
import matplotlib.pyplot as plt
import simpy

MAX_DISTANCE = 2000
sim_env = simpy.Environment()
environment = TempEnvironment(sim_env,  Location(MAX_DISTANCE, -MAX_DISTANCE), Location(-MAX_DISTANCE, MAX_DISTANCE), 296.15, dx = 50)

plt.ion()
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(1,1,1)
im = ax.imshow(environment.T, alpha=.5, interpolation='bicubic', cmap='RdYlGn_r', origin='lower'
,extent=[-MAX_DISTANCE, MAX_DISTANCE, - MAX_DISTANCE, MAX_DISTANCE]
)
ax.axes.xaxis.set_visible(False)
ax.axes.yaxis.set_visible(False)
plt.colorbar(im)
im.set_clim(353, 293)
plt.axis('off')
plt.draw()
plt.show()
contour_ax = fig.add_axes(ax.get_position(), frameon=False)
contour_ax.set_xlim([-MAX_DISTANCE, MAX_DISTANCE])
contour_ax.set_ylim([-MAX_DISTANCE, MAX_DISTANCE])
sim_env.process(environment.update( update_rate=60, im = im, ax = contour_ax))
sim_env.run(5*MINUTE_TO_MS)