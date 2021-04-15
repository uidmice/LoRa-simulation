import numpy as np
import matplotlib.pyplot as plt
import itertools
from Simulation import Simulation
from framework.utils import load_config, random_policy, field_construct_data
from config import *
import pickle

DEBUG = False

num_steps = 1000
step_time = 6000  # ms
offset = 3000
fire_update = 18000
config = 'config2'

gateway_location, node_locations, connection = load_config(config)
simulation = Simulation(node_locations, gateway_location, step_time, connection, config, offset=offset, update_rate=fire_update)
policy = lambda x: random_policy(0.5, x)
policy.name = "random_0.1"
# field_construct_data(simulation, num_steps, step_time/1000, policy, scale=100, show=True)

 # STATE_KEYWORDS = ["location", "failure_rate", "last_update", "current_sensing",
    #                   "num_unique_packets_received", "num_total_packets_sent", "total_transmit_time",
    #                   "total_receive_time", "total_energy_usage", "last_packet_success"]



repeat = 5
random_para = [0.1,0.2,0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
PER_random = np.zeros((len(random_para), repeat, num_steps))
pos_reward_random = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
success_nodes = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
send_nodes = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
real_field = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
constructed_field = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))

for j, prob in enumerate(random_para):
    print("Probability: "+ str(prob))
    for i in range(repeat):
        print('\t ' + str(i))
        simulation.reset()
        for k in range(num_steps):
            send, success = simulation.step(random_policy(prob, simulation))
            success_array = np.zeros(len(node_locations))
            send_array = np.zeros(len(node_locations))
            success_array[success] = 1
            send_array[send] = 1

            success_nodes[j, i, k, :] = success_array
            send_nodes[j,i,k,:] = send_array

            real_field[j, i, k, :] = np.fromiter(simulation.real_field.values(), dtype=float)
            constructed_field[j, i, k, :] = np.fromiter(simulation.constructed_field.values(), dtype=float)
            pos_reward = np.absolute(real_field[j, i, k, :] - constructed_field[j, i, k, :])

            pos_reward_random[j,i,k,:] = pos_reward * success_array
            n = max(len(send), 1)
            PER_random[j, i, k] = len(success) / n
name = "result/"+ simulation.name +"_random_full.pickle"
pickle.dump([PER_random, pos_reward_random, send_nodes, success_nodes, real_field, constructed_field], open(name, "wb"))


