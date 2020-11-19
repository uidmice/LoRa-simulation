import numpy as np
import matplotlib.pyplot as plt

from Simulation import Simulation
from framework.utils import Location, Tdiff_threshold_policy, print_statistics, GreedyPolicy, PER
from config import *

DEBUG = False

num_steps = 200
step_time = 6000  # ms
offset = 3000
node_locations = []
gateway_location = [Location(-1000, 1000), Location(1000, -1000)]
for i in range(-CORD + 5, CORD + 1, 7):
    for j in range(-CORD + 5, CORD + 1, 7):
        x = j * GRID
        y = i * GRID
        node_locations.append(Location(x, y))

simulation = Simulation(node_locations, gateway_location, step_time, offset=offset)
simulation.pre_adr(500, True)
simulation.reset()

 # STATE_KEYWORDS = ["location", "failure_rate", "last_update", "current_sensing",
    #                   "num_unique_packets_received", "num_total_packets_sent", "total_transmit_time",
    #                   "total_receive_time", "total_energy_usage", "last_packet_success"]

policy = GreedyPolicy(1000, node_locations)

performance = {"info_fresh": np.zeros((num_steps, len(node_locations))),
               "success_rate": np.zeros((num_steps, len(node_locations)))}
reward = np.zeros(num_steps)
iter_per = np.zeros(num_steps)
for i in range(num_steps):
    s = simulation.node_states("current_sensing", "last_update", "failure_rate")
    for j in range(len(node_locations)):
        performance['success_rate'][i, j] = 1 - s[j].failure_rate
        performance['info_fresh'][i, j] = np.exp(-np.absolute(s[j].last_update - s[j].current_sensing) / 20)
    action = policy.action_map(simulation)
    reward[i], iter_per[i] = simulation.step(action)
    # reward[i], iter_per[i] = simulation.step(Tdiff_threshold_policy(20, simulation))
    policy.update(simulation, action)

print("Total packet error rate: ", str(PER(simulation)))
# print_statistics(simulation,  num_steps)
# ani = PerformanceAnimation(node_locations, gateway_location, performance, step_time)
# ani.save("test.mp4")

fig,ax=plt.subplots()
ax.plot(reward, color="red")
ax.set_ylabel("reward",color="red",fontsize=14)
ax.set_xlabel("iterations")
ax2=ax.twinx()
ax2.plot(iter_per,color="blue")
ax2.set_ylabel("Packet error rate",color="blue",fontsize=14)
plt.show()
