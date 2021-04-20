import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image, matplotlib.axes
import math

from config import *

class Environment:
    def __init__(self, lower_right, upper_left, total_time):
        assert lower_right.x > upper_left.x, "lower right corner should have a greater x value"
        assert lower_right.y < upper_left.y, "lower right corner should have a smaller y value"
        self.lower_right = lower_right
        self.upper_left = upper_left
        self.total_time = total_time

    def sense(self, location, time) -> float:
        pass

    def reset(self, sim_env):
        pass

class ConstantEnvironment(Environment):
    def __init__(self, lower_right, upper_left, constant, total_time):
        super(ConstantEnvironment, self).__init__(lower_right, upper_left, total_time)
        self.constant = constant

    def sense(self, location, time):
        assert self.upper_left.x <= location.x <= self.lower_right.x, "x coordinate is out of bound"
        assert self.upper_left.y >= location.y >= self.lower_right.y, "y coordinate is out of bound"
        return self.constant

    def update(self, update_rate):
        return

    def reset(self, sim_env):
        return


class TempEnvironment(Environment):
    def __init__(self, lower_right, upper_left, init_temp, total_time: int, update_rate, dx = 1, v = np.array([1, 1])):
        super(TempEnvironment, self).__init__(lower_right, upper_left, total_time)
        self.dx = dx
        self.init_temp = init_temp
        self.T = np.ones((int((self.lower_right.x-upper_left.x)/self.dx) + 1, int((upper_left.y-lower_right.y)/self.dx) + 1))*init_temp

        x = range(int(upper_left.x/self.dx), int(lower_right.x/self.dx) + 1)
        y = range(int(lower_right.y/self.dx), int(upper_left.y / self.dx) + 1)
        self.xv, self.yv = np.meshgrid(x,y)

        n = np.random.randint(6, 10)
        self.k = np.zeros(self.T.shape)
        for i in range(n):
            xi = np.random.choice(x)
            yi = np.random.choice(y)
            self.k = self.generate(self.k, xi, yi)
        self.k = 1.3*n/(self.k+1.0)
        np.clip(self.k, 0.9, 2, out=self.k)

        xi = np.random.choice(x)
        yi = np.random.choice(y)

        self.H = 2.0/(0.003* (self.xv-xi)**2 + 0.004 * (self.yv-yi)**2+1)
        self.CG = np.ones(self.T.shape)*4

        self.v = v

        self.T_field = self.get_time_series_data(UPDATA_RATE, self.total_time//UPDATA_RATE)
        self.update_rate = update_rate

    def generate (self, k, x, y):
        alpha = np.random.random()/2000
        beta = np.random.random()/2000
        k += alpha * ((self.xv-x)/self.dx)**2 + beta * ((self.yv-y)/self.dx)**2
        return k


    def sense (self, location, time):
        assert self.upper_left.x <= location.x <= self.lower_right.x, "x coordinate is out of bound"
        assert self.upper_left.y >= location.y >= self.lower_right.y, "y coordinate is out of bound"
        cx = int(round((location.x - self.upper_left.x)/self.dx))
        cy = int(round((location.y - self.lower_right.y)/self.dx))

        return self.T_field[int(time//self.update_rate), cx, cy]


    # def get_temperature_by_index(self, location):
    #     x_max = int(math.ceil(location.x))
    #     x_min = int(math.floor(location.x))
    #     y_max = int(math.ceil(location.y))
    #     y_min = int(math.floor(location.y))
    #     return self.T


    def step(self, update_rate):
        self.T += self.H / 20
        # print("maximum T %.4f" %(np.max(self.T)))
        # print("minimum T %.4f" %(np.min(self.T)))
        avg = np.zeros((self.T.shape[0] + 2, self.T.shape[1] + 2))
        avg[1:-1, 1:-1] = self.T
        avg[1:-1, 0] = self.T[:, -1]
        avg[1:-1, -1] = self.T[:, 0]
        avg[0, 1:-1] = self.T[-1, :]
        avg[-1, 1:-1] = self.T[0, :]
        dT1 = avg[1:-1, 2:] - avg[1:-1, 1:-1]
        dT2 = avg[1:-1, 0:-2] - avg[1:-1, 1:-1]
        dT3 = avg[2:, 1:-1] - avg[1:-1, 1:-1]
        dT4 = avg[0:-2, 1:-1] - avg[1:-1, 1:-1]
        Q = np.multiply(self.k, (dT1 + dT2 + dT3 + dT4) / 4) * self.dx * update_rate / 2000
        self.T += np.divide(Q, self.CG)

    def get_time_series_data(self, update_rate, step):
        res = np.zeros((step, self.T.shape[0], self.T.shape[1]))
        for i in range(step):
            self.step(update_rate)
            res[i, :, :] = self.T
        return res

    # def update(self, update_rate = UPDATA_RATE):
    #     while True:
    #         yield self.sim_env.timeout(update_rate)
    #         self.step(60)
    #
    # def reset(self, sim_env):
    #     self.T = np.ones((int((self.lower_right.x - self.upper_left.x) / self.dx) + 1,
    #                       int((self.upper_left.y - self.lower_right.y) / self.dx) + 1)) * self.init_temp
    #     if sim_env:
    #         self.sim_env = sim_env

    def draw(self, frame_number, heat_map, fire_contour, time_text, update_rate):
        for i in range(6):
            self.step(update_rate)
        assert isinstance(heat_map, matplotlib.image.AxesImage)
        heat_map.set_data(self.T)
        if np.max(self.T) > 333:
            assert isinstance(fire_contour, matplotlib.axes.Axes)
            fire_contour.clear()
            fire_contour.contour(self.T, levels=[333], colors='red', linestyles='-')
        time_text.set_text(str(update_rate * 12 * frame_number/1000) + "s")


