import numpy as np
import matplotlib.pyplot as plt
from config import *


class RandomExternal:
    def __init__(self, sim_env, sigma = 0.5, eta = 0.2,gamma = 0.1, beta = 1):
        #f' = f + normal(sigma) + eta * df + gamma * (f-avg_surrondings)
        #df = f' - f
        #ranges [-2.5, 2.5]
        self.f = np.random.normal(size = (CORD +CORD + 1,CORD + CORD + 1))-1
        np.clip(self.f, -2.5, 2.5, out = self.f )
        self.df = np.zeros((2*CORD + 1, 2*CORD + 1))
        self.sigma = sigma
        self.eta = eta
        self.beta = beta
        self.sim_env = sim_env
        self.gamma = gamma

    def sense (self, x, y):
        cx = int(x/GRID)
        cy = int(y/GRID)
        value = self.f[cx+CORD, cy+CORD]
        return 1/(1+np.exp(-value * self.beta))

    def update(self, im = None):
        while True:
            yield self.sim_env.timeout(UPDATA_RATE)
            old_f = self.f
            avg = np.zeros((self.f.shape[0]+2, self.f.shape[1]+2))
            avg[1:-1,1:-1] = self.f
            avg[1:-1,0] = self.f[:,-1]
            avg[1:-1,-1] = self.f[:,0]
            avg[0, 1:-1] = self.f[-1,:]
            avg[-1,1:-1] = self.f[0,:]
            avg [1:-1,1:-1] = (avg[:-2,1:-1] + avg[2:,1:-1] + avg[1:-1, :-2] + avg[1:-1, 2:])/4
            self.f = self.f + np.random.normal(size = (2*CORD + 1, 2*CORD + 1))*self.sigma + self.df * self.eta + self.gamma * (self.f - avg [1:-1,1:-1])
            np.clip(self.f, -2.5, 2.5, out = self.f )
            self.df = self.f - old_f
            if im:
                im.set_data(self.f)
                plt.draw()
                plt.pause(0.001)
                plt.show()
