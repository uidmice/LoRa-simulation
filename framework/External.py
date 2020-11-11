import numpy as np
import matplotlib.pyplot as plt
from config import *
from mpl_toolkits import mplot3d

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

class ConstantExternal:
    def __init__(self, prob):
        self.prob = prob

    def sense (self, x, y):
        return self.prob



class TempExternal:
    def __init__(self, sim_env):
        self.T = np.ones((2*CORD + 1, 2*CORD + 1))*20
        self.dT = np.zeros((2*CORD + 1, 2*CORD + 1))
        self.A = GRID * GRID
        self.d = GRID
        self.sim_env = sim_env
        self.k = np.zeros((2*CORD + 1, 2*CORD + 1))
        x = range(-CORD, CORD+1)
        y = range(-CORD, CORD+1)
        self.xv, self.yv = np.meshgrid(x,y)
        n = np.random.randint(6, GRID/5)
        for i in range(n):
            xi = np.random.choice(x)
            yi = np.random.choice(y)
            self.k = self.generate(self.k, xi, yi)

        self.k = 1.3*n/(self.k+1)
        np.clip(self.k, 0.9, 2, out = self.k )

        xi = np.random.choice(range(-CORD+8, CORD-7))
        yi = np.random.choice(range(-CORD+8, CORD-7))

        self.H = 2.0/(0.003* (self.xv-xi)**2 + 0.004 * (self.yv-yi)**2+1)
        self.CG = np.ones(self.T.shape)*4


    def generate (self, k, x, y):
        alpha = np.random.random()/2000
        beta = np.random.random()/2000
        k += alpha * (self.xv-x)**2 + beta * (self.yv-y)**2
        return k


    def sense (self, x, y):
        cx = int(x/GRID)
        cy = int(y/GRID)
        value = self.T[cy+CORD, cx+CORD]
        return value

    def update(self, im = None, ax = None, status = None):
        while True:
            yield self.sim_env.timeout(UPDATA_RATE)

            self.T += self.H/20
            # print("maximum T %.4f" %(np.max(self.T)))
            # print("minimum T %.4f" %(np.min(self.T)))
            avg = np.zeros((self.T.shape[0]+2, self.T.shape[1]+2))
            avg[1:-1,1:-1] = self.T
            avg[1:-1,0] = self.T[:,-1]
            avg[1:-1,-1] = self.T[:,0]
            avg[0, 1:-1] = self.T[-1,:]
            avg[-1,1:-1] = self.T[0,:]
            dT1 = avg[1:-1,2:]-avg[1:-1,1:-1]
            dT2 = avg[1:-1,0:-2]-avg[1:-1,1:-1]
            dT3 = avg[2:,1:-1]-avg[1:-1,1:-1]
            dT4 = avg[0:-2,1:-1]-avg[1:-1,1:-1]
            Q = np.multiply(self.k ,(dT1+dT2+dT3+dT4)/4) * GRID * UPDATA_RATE/2000
            # print("maximum Q %.4f" %(np.max(Q)))
            # print("minimum Q %.4f" %(np.min(Q)))
            if np.any(np.isnan(Q)):
                print(Q)
                input('Press Enter to continue ...')

            self.T += np.divide(Q,self.CG)

            if im and ax and status:
                im.set_data(self.T)
                if (np.max(self.T)>60):
                    ax.clear()
                    ax.contour(self.T, levels=[60], colors='red', linestyles='-')
                    ax.axes.xaxis.set_visible(False)
                    ax.axes.yaxis.set_visible(False)
                # im.set_clim(np.max(self.T)+3, np.min(self.T))
                status.patches.set_array(status.transmission)
                plt.draw()
                plt.pause(0.001)
                plt.show()
            elif im and ax:
                im.set_data(self.T)
                if (np.max(self.T)>60):
                    ax.clear()
                    ax.contour(self.T, levels=[60], colors='red', linestyles='-')
                # im.set_clim(np.max(self.T)+3, np.min(self.T))
                plt.draw()
                plt.pause(0.001)
                plt.show()
