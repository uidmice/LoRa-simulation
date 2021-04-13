from framework.Environment import TempEnvironment
from framework.utils import Location
from config import *
import matplotlib.pyplot as plt
import numpy as np
import math
import random
import itertools
from matplotlib.animation import FuncAnimation
plt.style.use('seaborn-pastel')

init_temp = 296.15
T = 1000
g = 128 # number of transmission per unit of time
temp_field = TempEnvironment(None, Location(MAX_DISTANCE, -MAX_DISTANCE),Location(-MAX_DISTANCE, MAX_DISTANCE), init_temp , dx=GRID)
temps = temp_field.get_time_series_data(UPDATA_RATE, T)

def three_points_plane(location1, location2, location3, z1, z2, z3):
    # ax + by + cz - d = 0
    p1 = np.array([location1.x, location1.y, z1])
    p2 = np.array([location2.x, location2.y, z2])
    p3 = np.array([location3.x, location3.y, z3])
    cp = np.cross(p3 - p1, p2 - p1)
    a, b, c = cp
    d = np.dot(cp, p3)
    return a, b, c, d

class Device:
    class State:
        def __init__(self, location, s, ds, t):
            self.location = location
            self.s = s
            self.ds = ds
            self.t = t

        def __str__(self):
            return "(%.1f, %.1f), s = %.3f, ds = %.3f, t = %d" %(self.location.x, self.location.y, self.s, self.ds, self.t)

    def __init__(self, id, location: Location, init_temp, temp_data, alpha_l = 1, alpha_n=0.8, beta_n=0.8):
        self.id = id
        self.state = self.State(location, init_temp, 0, 0)
        self.temp_data = temp_data
        self.alpha_l = alpha_l
        self.alpha_n = alpha_n
        self.beta_n = beta_n
        self.nearby_devices = {}

    def _get_local_temp(self, time):
        x_max = int(math.ceil(self.state.location.x))
        x_min = int(math.floor(self.state.location.x))
        y_max = int(math.ceil(self.state.location.y))
        y_min = int(math.floor(self.state.location.y))
        return (self.temp_data[time, x_max,y_max]+self.temp_data[time, x_max,y_min]+self.temp_data[time, x_min,y_max]+self.temp_data[time, x_min,y_min])/4

    def connect(self, other):
        self.nearby_devices[other] = other.state
        other.nearby_devices[self] = self.state

    def update(self, time):
        temp = self._get_local_temp(time)
        self.state.ds = (1 - self.alpha_l) * self.state.ds + self.alpha_l * (temp - self.state.s) / (time - self.state.t)
        self.state.t = time
        self.state.s = temp
        print(self.state)
        # for d in self.nearby_devices:
        #     d.nearby_update(time)
        return

    def nearby_update(self, time):
        if len(self.nearby_devices) > 2:
            nearby_states = list(self.nearby_devices.values())
            nearby_states.sort(key=lambda x: x.t, reverse=True)
            z1 = nearby_states[0].s + nearby_states[0].ds * (time - nearby_states[0].t)
            z2 = nearby_states[1].s + nearby_states[1].ds * (time - nearby_states[1].t)
            z3 = nearby_states[2].s + nearby_states[2].ds * (time - nearby_states[2].t)
            # ax + by + cz - d = 0
            a, b, c, d = three_points_plane(nearby_states[0].location, nearby_states[1].location, nearby_states[2].location, z1, z2, z3)
            s_est = (d - a * self.state.location.x - b * self.state.location.y) / c
            if math.isnan((s_est)):
                print(str(nearby_states[0]) + '  ' + str(z1))
                print(str(nearby_states[1]) + '  ' + str(z2))
                print(str(nearby_states[2]) + '  ' + str(z3))
            print(s_est)
            a, b, c, d = three_points_plane(nearby_states[0].location, nearby_states[1].location,
                                            nearby_states[2].location, nearby_states[0].ds, nearby_states[1].ds, nearby_states[2].ds)
            ds_est = (d - a * self.state.location.x - b * self.state.location.y) / c
            print(ds_est)
            self.state.s = (1 - self.beta_n)* (self.state.s + self.state.ds * (time - self.state.t)) + self.beta_n * s_est
            self.state.ds = (1 - self.alpha_n) * self.state.ds + self.alpha_n * ds_est
            self.state.t = time
        else:
            self.state.s = self.state.s + self.state.ds * (time - self.state.t)
            self.state.t = time



LENGTH = 81
devices = {}
X_position = np.arange(4.5, LENGTH, 6)
N = len(X_position)
for i, x in enumerate(X_position):
    devices[i] = []
    for j, y in enumerate(X_position):
        x1 = min(max(x + np.random.normal(scale=2), 0.1), LENGTH-1.2)
        y1 = min(max(x + np.random.normal(scale=2), 0.1), LENGTH-1.2)
        n = Device(i * N + j, Location(x1,y1), init_temp, temps)
        devices[i].append(n)
        if i > 0:
            n.connect(devices[i-1][j])
            if j > 0:
                n.connect(devices[i-1][j - 1])
            if j < len(X_position) - 1:
                n.connect(devices[i-1][j + 1])
        if j > 0:
            n.connect(devices[i][j - 1])

devices = list(itertools.chain.from_iterable(devices.values()))
X, Y = np.meshgrid(X_position, X_position)
Z = np.zeros((T, X.shape[0], X.shape[1]))
# for i, device in enumerate(devices):
#     print("Device %f @ (%.1f, %.1f)" %(device.id, device.state.location.x, device.state.location.y))
#     print("(%.1f, %.1f)" %(X[i%N][i//N], Y[i%N][i//N]))
chosen = random.sample(range(len(devices)), int(g))
for t in range(T-1):
    nearby = set()
    for i in chosen:
        devices[i].update(t+1)
        nearby = nearby.union(devices[i].nearby_devices.keys())
    for d in nearby:
        d.nearby_update(t+1)
    S = [a.state.s for a in devices]
    Z[t,:,:] = np.reshape(S, X.shape)
    chosen = [i for i, value in enumerate(sorted(devices, key=lambda x: x.state.ds, reverse=True))][:int(g)]


# x = np.arange(LENGTH)
# X, Y = np.meshgrid(x, x)
fig = plt.figure()
ax = plt.axes(projection='3d')
cont = ax.contour3D(X, Y, Z[0,:,:], 50, cmap='binary')
#
def animate(i):
    ax.clear()
    ax.contour3D(X, Y, Z[i, :, :], 50, cmap='binary')
    ax.set_title("t = %d" %(i))

anim = FuncAnimation(fig, animate, frames=temps.shape[0], interval=200)
plt.show()
# anim.save('sine_wave.gif', writer='imagemagick')
