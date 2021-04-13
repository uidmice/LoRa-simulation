from framework.Environment import TempEnvironment
from framework.utils import Location
from config import *
import matplotlib.pyplot as plt
import numpy as np
import math
import cvxpy as cp
import random
import itertools
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation

plt.style.use('seaborn-pastel')



class Estimator:
    def __init__(self, init_temp=296.15, T=1000, size=MAX_DISTANCE*2, n_device=10):
        self.init_temp = init_temp
        self.T = T
        self.temp_field = TempEnvironment(None, Location(size/2, -size/2),Location(-size/2, size/2), init_temp , dx=GRID)
        self.temps = self.temp_field.get_time_series_data(UPDATA_RATE, T)
        self.N = self.temps.shape[1]
        self.n = n_device
        assert self.n <= self.N
        idx = np.arange(self.n**2).reshape((self.n,self.n))
        self.L = np.identity(self.n**2) * (-4)
        for i in range(self.n):
            for j in range(self.n):
                self.L[idx[i][j]][idx[i][(j + 1)%self.n]] = 1
                self.L[idx[i][j]][idx[i][j - 1]] = 1
                self.L[idx[i][j]][idx[(i + 1)%self.n][j]] = 1
                self.L[idx[i][j]][idx[i - 1][j]] = 1
        self.q = np.zeros(len(self.L))
        self.dq = np.zeros(self.q.shape)
        self.dL = np.zeros(self.L.shape)
        self.count = 0
        self.y = np.ones(self.q.shape) * init_temp
        distance = self.N//self.n
        self.position_idx = np.arange(self.N%self.n, self.N, distance, dtype='int')
        self.measured = self.temps[:,self.position_idx]
        self.measured = self.measured[:,:,self.position_idx]
        print(self.measured.shape)

    def step_q(self, percentage):
        if self.count +1< self.T:
            self.count += 1
            self.L = self.L + self.dL
            q1 = self.q + self.dq
            self.y = self.y + self.L @ self.y + self.q
            assert 0 < percentage <= 1
            n = int(len(self.q) * percentage)
            selected = np.random.randint(self.temps.shape[1]*self.temps.shape[2], size=n)
            y_p = self.y[selected]
            y_t = self.temps[self.count].reshape(-1)[selected]
            ddq = y_t - y_p
            self.dq[selected] += ddq
            q1[selected] += y_t - y_p
            self.q = q1

    def step_L(self, percentage, K):
        if self.count +K < self.T:
            assert 0 < percentage <= 1
            y_t = np.zeros(( K, len(self.q)))
            y_d = np.zeros(y_t.shape)
            for i in range(K):
                n = int(len(self.q) * percentage)
                selected = np.random.randint(self.temps.shape[1] * self.temps.shape[2], size=n)
                y_t[i][selected] = self.temps[self.count].reshape(-1)[selected]
                self.count += 1
                self.L = self.L + self.dL
                self.q = self.q + self.dq
                self.y = self.y + self.L @ self.y + self.q
                y_d[i][selected] = self.temps[self.count].reshape(-1)[selected] - self.y[selected]
                self.y[selected] = self.temps[self.count].reshape(-1)[selected]
            ddl = np.linalg.pinv(y_t) @ y_d
            self.L += K * ddl
            self.dL += ddl

    def step(self, percentage):
        if self.count + 1 < self. T:
            assert 0 < percentage <= 1
            n = int(len(self.q) * percentage)
            selected = np.random.choice(self.n**2, size=n, replace=False)
            self.count += 1
            y1 = np.reshape(self.y[selected], (n, 1))
            # self.L = self.L + self.dL
            # self.q = self.q + self.dq
            self.y = self.y + self.L @ self.y + self.q
            y2 = np.reshape(self.measured[self.count].reshape(-1)[selected] - self.y[selected], (n,1))
            self.y[selected] = self.measured[self.count].reshape(-1)[selected]

            # L = np.copy(self.L)
            # q = np.copy(self.q)

            ddl = cp.Variable((n, n))
            ddq = cp.Variable((n,1))

            gamma = cp.Parameter(nonneg=True)
            beta = cp.Parameter(nonneg=True)
            objective = cp.Minimize( cp.norm(ddl , 'fro')/n/n + n * cp.norm(ddq))
            constraints =[ddl @ y1 + ddq == y2]
            for i in range(n):
                constraints += [cp.sum(ddl[:,i])==0, cp.sum(ddl[i,:])==0]
            prob = cp.Problem(objective, constraints)
            prob.solve()

            if ddl.value is not None:
                for i, j in enumerate(selected):
                    self.L[j][selected] += ddl.value[i]
            if ddq.value is not None:
                self.q[selected] += ddq.value.reshape(n)
            # error_pred = []
            # optimal = []
            gamma_vals = np.arange(0,1,0.1)
            # for val in gamma_vals:
            #     # print("Gamma = %d" %(val))
            #     gamma.value = val
            #     beta.value = 1 - val
            #     prob.solve()
            #     # print("status:", prob.status)
            #     # print("optimal value", prob.value)
            #     optimal.append(prob.value)
            #     L[selected][selected] = ddl.value
            #     q[selected] = ddq.value.reshape(n)
            #     yp = self.y + L @ self.y + q
            #     error_pred.append(sum(np.absolute(yp - self.measured[self.count+1].reshape(-1))))

            # plt.figure(figsize=(6, 10))
            #
            # # Plot trade-off curve.
            # plt.subplot(211)
            # plt.plot(error_pred, optimal)
            # plt.xlabel('Error', fontsize=16)
            # plt.ylabel('Optimal', fontsize=16)
            # plt.title('Trade-Off Curve', fontsize=16)
            #
            # # Plot entries of x vs. gamma.
            # ax = plt.subplot(212)
            # ax.plot(gamma_vals, optimal, color="red")
            # ax.set_ylabel("Optimal", color="red", fontsize=14)
            # ax.set_xlabel('Gamma', fontsize=14)
            # ax1 = ax.twinx()
            # ax1.plot(gamma_vals, error_pred, color="blue")
            # ax1.set_ylabel("Error", color="blue", fontsize=14)
            # plt.show()

# estimator = Estimator(T=300, n_device=12)
# reconstruction = np.zeros((estimator.T, estimator.n, estimator.n))
# simulated = estimator.measured
# assert reconstruction.shape == simulated.shape
# count = estimator.T
# for t in range(estimator.T-1):
#     print(t)
#     try:
#         estimator.step(1)
#         reconstruction[t, :, :, ] = np.reshape(estimator.y, (estimator.n, estimator.n))
#     except cp.error.SolverError:
#         count = t
#         break
#
#
# X, Y = np.meshgrid(estimator.position_idx, estimator.position_idx)
# fig = plt.figure(figsize=(15,5))
# ax1 = fig.add_subplot(1, 3, 1, projection='3d')
# ax2 = fig.add_subplot(1, 3, 2, projection='3d')
# ax3 = fig.add_subplot(1, 3, 3, projection='3d')
# # ax = plt.axes(projection='3d')
# ax1.contour3D(X, Y, reconstruction[0,:,:], 50, cmap='binary')
# ax2.contour3D(X, Y, simulated[0,:,:], 50, cmap='bwr')
# ax3.contour3D(X, Y, simulated[0,:,:] - reconstruction[0,:,:], 50, cmap='binary')
#
# def animate(i):
#     ax1.clear()
#     ax2.clear()
#     ax3.clear()
#     ax1.contour3D(X, Y, reconstruction[i, :, :], 50, cmap='binary')
#     ax2.contour3D(X, Y, simulated[i, :, :], 50, cmap='bwr')
#     ax3.contour3D(X, Y, simulated[i, :, :] - reconstruction[i, :, :], 50, cmap='binary')
#     fig.suptitle("t = %d" %(i))
#
# anim = FuncAnimation(fig, animate, frames=count -1, interval=200)
# plt.show()
#
g = 60
#
class Device:
    class State:
        def __init__(self, location, s, r, t):
            self.location = location
            self.s = s
            self.t = t
            self.es_s_change = 0


        def __str__(self):
            return "(%.1f, %.1f), s = %.3f, ds = %.3f, t = %d" %(self.location.x, self.location.y, self.s, self.ds, self.t)

    def __init__(self, id, location: Location, init_temp, temp_data):
        self.id = id
        self.state = self.State(location, init_temp, 0, 0)
        self.temp_data = temp_data
        self.device_index = {}
        self.w = []
        self.dw = np.array([])
        self.ds = {}
        self.hist = []


    def _get_local_temp(self, time):
        x_max = int(math.ceil(self.state.location.x))
        x_min = int(math.floor(self.state.location.x))
        y_max = int(math.ceil(self.state.location.y))
        y_min = int(math.floor(self.state.location.y))
        return (self.temp_data[time, x_max,y_max]+self.temp_data[time, x_max,y_min]+self.temp_data[time, x_min,y_max]+self.temp_data[time, x_min,y_min])/4

    def connect(self, other):
        self.device_index[other] = len(self.w)
        other.device_index[self] = len(other.w)
        self.w.append(0.1)
        other.w.append(0.1)
        self.hist.append(0)
        other.hist.append(0)

    def update(self, time):
        temp = self._get_local_temp(time)
        self.ds[(temp - self.state.s)/(time - self.state.t)] = self.hist
        self.state.s = temp
        self.state.t = time
        self.es_s_change = 0
        self.hist = np.zeros(len(self.w))
        for d in self.device_index:
            d.nearby_update(self)
        if len(self.ds) == 6:
            M = np.array([self.ds[a] for a in self.ds])
            w = np.linalg.pinv(M) @ np.array([[a for a in self.ds]]).T
            self.dw = w - np.array(self.w)
            self.w = w
            self.ds = {}
            # print(self.w)

        return

    def nearby_update(self, update_device):
        assert update_device in self.device_index, "Nearby update from unconnected device"
        idx = self.device_index[update_device]
        self.hist[idx] += (update_device.state.s - self.state.s)/max(update_device.state.t - self.state.t, 1)

    def get_temp(self, time):
        nearby_s = np.array([[a.state.s for a in self.device_index]])
        return self.state.s + (time - self.state.t) * np.dot(nearby_s- self.state.s, np.array(self.w))
        # return self.state.s


estimator = Estimator()
LENGTH = 81
devices = {}
X_position = np.arange(4.5, LENGTH, 6)
N = len(X_position)
for i, x in enumerate(X_position):
    devices[i] = []
    for j, y in enumerate(X_position):
        # x1 = min(max(x + np.random.normal(scale=2), 0.1), LENGTH-1.2)
        # y1 = min(max(x + np.random.normal(scale=2), 0.1), LENGTH-1.2)
        n = Device(i * N + j, Location(x,y), estimator.init_temp, estimator.temps)
        devices[i].append(n)
        if i > 0:
            n.connect(devices[i-1][j])
        if j > 0:
            n.connect(devices[i][j - 1])
for i, d in enumerate(devices[0]):
    d.connect(devices[N -1][i])
    devices[i][0].connect(devices[i][N - 1])

devices = list(itertools.chain.from_iterable(devices.values()))
X, Y = np.meshgrid(X_position, X_position)
Z = np.zeros((estimator.T, X.shape[0], X.shape[1]))
Tr = np.zeros((estimator.T, X.shape[0], X.shape[1]))
# for i, device in enumerate(devices):
#     print("Device %f @ (%.1f, %.1f)" %(device.id, device.state.location.x, device.state.location.y))
#     print("(%.1f, %.1f)" %(X[i%N][i//N], Y[i%N][i//N]))
chosen = random.sample(range(len(devices)), int(g))

for t in range(estimator.T-1):
    for i in chosen:
        devices[i].update(t+1)
    S = [a.get_temp(t+1) for a in devices]
    Temp = [a._get_local_temp(t+1) for a in devices]
    Z[t,:,:] = np.reshape(S, X.shape)
    Tr[t, :, :] = np.reshape(Temp, X.shape)
    chosen = random.sample(range(len(devices)), 60)


x = np.arange(LENGTH)
X1, Y1 = np.meshgrid(x, x)
fig = plt.figure(figsize=(15,5))
ax1 = fig.add_subplot(1, 3, 1, projection='3d')
ax2 = fig.add_subplot(1, 3, 2, projection='3d')
ax3 = fig.add_subplot(1, 3, 3, projection='3d')
# ax = plt.axes(projection='3d')
cont = ax1.contour3D(X, Y, Z[0,:,:], 50, cmap='binary')
ax2.contour3D(X, Y, Tr[0,:,:], 50, cmap='bwr')
ax3.contour3D(X, Y, Tr[0,:,:] - Z[0,:,:], 50, cmap='binary')

def animate(i):
    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax1.contour3D(X, Y, Z[i, :, :], 50, cmap='binary')
    ax2.contour3D(X, Y, Tr[i, :, :], 50, cmap='bwr')
    ax3.contour3D(X, Y, Tr[i, :, :] - Z[i, :, :], 50, cmap='binary')

    fig.suptitle("t = %d" %(i))

anim = FuncAnimation(fig, animate, frames=estimator.temps.shape[0], interval=200)
plt.show()
# writer = animation.writers['ffmpeg']
# writer = writer(fps=10, metadata=dict(artist='Me'), bitrate=900)
# anim.save('predict.mp4', writer='ffmpeg')
