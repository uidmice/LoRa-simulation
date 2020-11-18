import numpy as np
import matplotlib.pyplot as plt

from Simulation import Simulation, PerformanceAnimation
from framework.TransmissionInterface import Location
from config import *

DEBUG = False

num_steps = 200
step_time = 6000 # ms
node_locations = []
gateway_location = [Location(0, 0)]
for i in range(-CORD + 5, CORD + 1, 10):
    for j in range(-CORD + 5, CORD + 1, 10):
        x = j * GRID
        y = i * GRID
        node_locations.append(Location(x, y))

simulation = Simulation(node_locations, gateway_location, step_time)


def T_threshold_policy(T_threshold, states):
    action = []
    for s in states:
        if s.current_sensing > T_threshold:
            action.append(True)
        else:
            action.append(False)
    return action


def Tdiff_threshold_policy(T_threshold, states):
    action = []
    for s in states:
        if np.absolute(s.current_sensing - s.last_update) > T_threshold:
            action.append(True)
        else:
            action.append(False)
    return action

performance ={"info_fresh": np.zeros((num_steps, len(node_locations))), "success_rate":np.zeros((num_steps, len(node_locations)))}
reward = np.zeros(num_steps)
for i in range(num_steps):
    s = simulation.node_states("current_sensing", "last_update", "failure_rate")
    # STATE_KEYWORDS = ["location", "failure_rate", "last_update", "current_sensing",
    #                   "num_unique_packets_received", "num_total_packets_sent", "total_transmit_time",
    #                   "total_receive_time", "total_energy_usage"]
    for j in range(len(node_locations)):
        performance['success_rate'][i, j] = 1- s[j].failure_rate
        performance['info_fresh'][i, j] = np.exp(-np.absolute(s[j].last_update - s[j].current_sensing)/20)

    reward[i] = simulation.step(Tdiff_threshold_policy(20, s))

statistics = simulation.node_states("num_total_packets_sent", "num_unique_packets_received", "total_transmit_time",
                                    "total_energy_usage")
print('Of ', str(len(node_locations)), ' nodes:')
print("Numbers of packets sent:")
print([s.num_total_packets_sent for s in statistics])
print("Numbers of packets successfully received:")
print([s.num_unique_packets_received for s in statistics])
print("Total transmission time: (s)")
print([s.total_transmit_time / 1000.0 for s in statistics])
print("Total energy consumption: (J)")
print([s.total_energy_usage / 1000.0 for s in statistics])
print('')

tol_sent = sum([s.num_total_packets_sent for s in statistics])
tol_receive = sum([s.num_unique_packets_received for s in statistics])
ave_e = np.average([s.total_energy_usage / 1000.0 for s in statistics])
max_e = np.max([s.total_energy_usage / 1000.0 for s in statistics])
print("Total number of packets sent: ", tol_sent)
print("Total number of packets successfully received: ", tol_receive)
print("Average duty circle: ",
      np.average([s.total_transmit_time / 1000.0 for s in statistics]) / (num_steps * step_time) * 100, "%")
print("Average energy consumption: {:.2f}(mJ), {:.6f}% ".format(ave_e, ave_e / BATTERY_ENERGY * 100))
print("Maximum energy consumption: {:.2f}(mJ), {:.6f}%".format(max_e, max_e / BATTERY_ENERGY * 100))
print("Success ratio: {:.2f}%".format(tol_receive * 1.0 / tol_sent * 100))


ani = PerformanceAnimation(node_locations, gateway_location, performance, step_time)
ani.save("test.mp4")

plt.close("all")
plt.figure()
plt.plot(reward)
plt.show()