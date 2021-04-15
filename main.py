import numpy as np
import matplotlib.pyplot as plt
import itertools
from Simulation import Simulation
from framework.utils import Location, Tdiff_threshold_policy, print_statistics, GreedyPolicy, PER, random_policy, T_threshold_policy
from config import *
import pickle

DEBUG = False

Z, tr = pickle.load(open("result/config2_update_18000_field_random_0.1.pkl", 'rb'))
diff = Z - tr
plt.ion()
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(1,1,1)

for i in range(Z.shape[0]):
    plt.imshow(diff[i], cmap='hot')
    plt.colorbar()
    plt.draw()
    plt.pause(0.02)

