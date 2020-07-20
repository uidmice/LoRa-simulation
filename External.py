import numpy as np
import matplotlib.pyplot as plt
from config import *


class RandomExternal:
    def __init__(self, sim_env, sigma = 0.3, eta = 0.2, beta = 1):
        #f' = f + normal(sigma) + eta * df
        #df = f' - f
        #ranges [-2.5, 2.5]
        self.f = np.random.normal(size = (CORD +CORD + 1,CORD + CORD + 1))-1
        np.clip(self.f, -2.5, 2.5, out = self.f )
        self.df = np.zeros((2*CORD + 1, 2*CORD + 1))
        self.sigma = sigma
        self.eta = eta
        self.beta = beta
        self.sim_env = sim_env

    def sense (self, x, y):
        cx = int(x/GRID)
        cy = int(y/GRID)
        value = self.f[cx+CORD, cy+CORD]
        return 1/(1+np.exp(-value * self.beta))

    def update(self, im = None):
        while True:
            yield self.sim_env.timeout(UPDATA_RATE)
            old_f = self.f
            self.f = self.f + np.random.normal(size = (2*CORD + 1, 2*CORD + 1))*self.sigma + self.df * self.eta
            np.clip(self.f, -2.5, 2.5, out = self.f )
            self.df = self.f - old_f
            if im:
                im.set_data(self.f)
                plt.draw()
                plt.pause(0.001)
                plt.show()
