import simpy
import matplotlib.animation as animation
from scipy import interpolate
import numpy as np

from framework.Node import Node, EnergyProfile
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface, Location
from framework.Server import Server, Application
from framework.LoRaParameters import LoRaParameters
from framework.Environment import *


class Simulation:
    ENVIRONMENT_TYPE = ["temp"]

    def __init__(self, nodes_positions, gateway_positions, step_time, environment="temp", offset=2000):
        self.nodes = []
        self.gateways = []
        assert step_time >= offset + 3000
        self.step_time = step_time
        self.offset = offset
        self.steps = 0
        self.sim_env = simpy.Environment()
        assert environment in Simulation.ENVIRONMENT_TYPE
        if environment == "temp":
            self.environment = TempEnvironment(self.sim_env, Location(MAX_DISTANCE, -MAX_DISTANCE),
                                               Location(-MAX_DISTANCE, MAX_DISTANCE), 296.15, dx=GRID)
        else:
            assert False
        self.sim_env.process(self.environment.update(UPDATA_RATE))
        self.server = Server(self.gateways, self.sim_env, Application())
        self.air_interface = AirInterface(self.sim_env, self.gateways, self.server)
        for i in range(len(nodes_positions)):
            self.nodes.append(Node(i, EnergyProfile(0.1), LoRaParameters(i % Gateway.NO_CHANNELS, sf=12),
                                   self.air_interface, self.sim_env, nodes_positions[i], True))
        for i in range(len(gateway_positions)):
            self.gateways.append(Gateway(i, gateway_positions[i], self.sim_env))

        # states:
        self.num_packet_sent_given_nearby = {}
        self.num_packet_sent_suc_given_nearby = {}
        for i in [a.id for a in self.nodes]:
            self.num_packet_sent_given_nearby[i] = {}
            self.num_packet_sent_suc_given_nearby[i] = {}
            for j in range(30):
                self.num_packet_sent_given_nearby[i][j] = 2
                self.num_packet_sent_suc_given_nearby[i][j] = 2

    def node_states(self, *args, **kwargs):
        return list(a.get_status(*args, **kwargs) for a in self.nodes)

    def step(self, actions):
        assert len(self.nodes) == len(actions)
        assert self.sim_env.now == self.steps * self.step_time
        self.steps += 1
        for i in range(len(self.nodes)):
            self.sim_env.process(self._node_send(i, actions[i]))
        self.sim_env.run(self.step_time * self.steps)

    def _node_send(self, node_index, send):
        yield self.sim_env.timeout(np.random.randint(self.offset))
        node = self.nodes[node_index]
        value = node.sense(self.environment)
        if send:
            packet = node.create_unique_packet(value, True, True)
            yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

class Animation:
    def __init__(self, node_location: list, gateway_location: list, performance: dict, step_size,fps=10):
        self.gateway_location = gateway_location
        self.x = list(n.x for n in node_location)
        self.y = list(n.y for n in node_location)
        self.step_size = step_size
        self.fps = fps
        self.figure = plt.figure(0, figsize=(18,9))
        self.ax1 = self.figure.add_subplot(1, 2, 1, projection='3d')
        self.ax2 = self.figure.add_subplot(1, 2, 1, projection='3d')
        axtext = self.figure.add_axes([0.0, 0.95, 0.1, 0.05])
        axtext.axis("off")
        self.info_fresh = performance["info_fresh"]
        self.success_rate = performance["success_rate"]
        assert self.info_fresh.shape[0] == self.success_rate.shape[0]
        self.frn = self.info_fresh.shape[0]
        self.time_label = axtext.text(0.5, 0.5, "0s", ha="left", va="top")
        self.writer = None
        Writer = animation.writers['ffmpeg']
        self.writer = Writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)


    def _update_plot(self, frame_number):
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.set_title("Success rate")
        self.ax2.set_title(r"$\exp{-|dT|/10}}$")

        self.ax1.scatter3D(self.x, self.y, self.success_rate[frame_number, :],  cmap="winter_r", c = self.success_rate[frame_number, :], vmin=0, vmax=2)
        self.ax2.scatter3D(self.x, self.y, self.info_fresh[frame_number, :],  cmap="winter_r", c = self.info_fresh[frame_number, :], vmin=0, vmax=2)
        self.ax1.set_zlim(0,1.1)
        self.ax2.set_zlim(0,1.1)
        self.time_label.set_text(str(frame_number * self.step_size/1000) + "s")

    def play(self):
        self.ax1.set_title("Success rate")
        self.ax2.set_title(r"$\exp{-|dT|/10}}$")
        self.ax1.scatter3D(self.x, self.y, self.success_rate[0, :], cmap="winter_r",
                           c=self.success_rate[0, :], vmin=0, vmax=2)
        self.ax2.scatter3D(self.x, self.y, self.info_fresh[0, :], cmap="winter_r",
                           c=self.info_fresh[0, :], vmin=0, vmax=2)
        self.ax1.set_zlim(0, 1.1)
        self.ax2.set_zlim(0, 1.1)
        animation.FuncAnimation(self.figure, self._update_plot, self.frn, interval=2000/self.fps)
        plt.figure(0)
        plt.show()

    def save(self, title):
        ani = animation.FuncAnimation(self.figure, self._update_plot, self.frn, interval=2000 / self.fps)
        ani.save(title, writer = self.writer)