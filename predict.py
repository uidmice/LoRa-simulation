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
config = 'config1'
gateway_location, node_locations, connection = load_config('config1')
simulation = Simulation(node_locations, gateway_location, step_time, connection, config, offset=offset)
# field_construct_data(simulation, num_steps, 0.5, True, scale=100)

 # STATE_KEYWORDS = ["location", "failure_rate", "last_update", "current_sensing",
    #                   "num_unique_packets_received", "num_total_packets_sent", "total_transmit_time",
    #                   "total_receive_time", "total_energy_usage", "last_packet_success"]



repeat = 5
random_para = [0.1,0.2,0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
per_random = np.zeros((len(random_para), repeat, num_steps))
pos_reward_random = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
received_nodes = np.zeros((len(random_para), repeat, num_steps, len(node_locations)))
for j, prob in enumerate(random_para):
    print("Probability: "+ str(prob))
    for i in range(repeat):
        print('\t ' + str(i))
        simulation.reset()
        for k in range(num_steps):
            send, success = simulation.step(random_policy(prob, simulation))
            pos_reward = simulation.eval_positive()
            receive = np.zeros(len(node_locations))
            receive[success] = 1
            received_nodes[j,i,k,:] = receive
            pos_reward_random[j,i,k,:] = pos_reward * receive
            n = max(len(send), 1)
            per_random[j,i,k] = len(success)/n
pickle.dump([per_random, pos_reward_random, received_nodes], open("result/random.pkl", "wb"))


