import numpy as np
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import enum, math

from config import *


def airtime(sf, bw, cr, h, de, pl):
    Npream = 8  # number of preamble symbol (12.25  from Utz paper)
    Tsym = (2.0 ** sf) / bw  # msec
    Tpream = (Npream + 4.25) * Tsym
    payloadSymbNB = 8 + max(
        math.ceil(
            (
                    8.0 * pl - 4.0 * sf + 28 - 20 * h) / (
                    4.0 * (sf - 2 * de)))
        * (cr + 4), 0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload  # msec


def PER(simulation):
    statistics = simulation.node_states("num_total_packets_sent", "num_unique_packets_received")
    sent = np.array([s.num_total_packets_sent for s in statistics])
    lost = sent - np.array([s.num_unique_packets_received for s in statistics])
    return np.sum(lost) /np.sum(sent)


class GreedyPolicy:
    def __init__(self, distance, node_locations):
        assert distance > 0
        self.distance = distance
        self.nearby_nodes = {}
        self.num_packet_sent_given_nearby = {}
        self.num_packet_sent_suc_given_nearby = {}
        for i in range(len(node_locations)):
            self.nearby_nodes[i] = []
            self.num_packet_sent_given_nearby[i] = {}
            self.num_packet_sent_suc_given_nearby[i] = {}

        for i in range(len(node_locations)):
            for j in range(i+1, len(node_locations)):
                if node_locations[i].distance(node_locations[j]) < self.distance:
                    self.nearby_nodes[i].append(j)
                    self.nearby_nodes[j].append(i)
        for i in range(len(node_locations)):
            for j in range(len(self.nearby_nodes[i]) + 1):
                self.num_packet_sent_given_nearby[i][j] = 2
                self.num_packet_sent_suc_given_nearby[i][j] = 2
        # for i in range(len(node_locations)):
        #     print(self.nearby_nodes[i])

    def update(self, simulation, actions):
        states = simulation.node_states("last_packet_success")
        for i in range(len(states)):
            if actions[i]:
                nearby = self.nearby_nodes[i]
                count = 0 # num of nearby nodes sending at the same time slot
                for node in nearby:
                    if actions[node]:
                        count += 1
                if not self.num_packet_sent_given_nearby[i][count]:
                    self.num_packet_sent_given_nearby[i][count] = 2
                    self.num_packet_sent_suc_given_nearby[i][count] = 2
                self.num_packet_sent_given_nearby[i][count] += 1
                if states[i].last_packet_success:
                    self.num_packet_sent_suc_given_nearby[i][count] += 1

    def action_map(self, simulation):
        selected = []
        states = simulation.node_states("failure_rate", "last_update", "current_sensing")
        action = list(False for i in range(len(states)))
        while len(selected) < len(states):
            indx_DT = [(s.id, np.absolute(s.current_sensing - s.last_update)) for s in states if s.id not in selected]
            n0 = [a[0] for a in indx_DT if a[1]==np.max([b[1] for b in indx_DT])][0]
            selected.append(n0)
            action[n0] = True
            num_nearby = np.amax(np.argwhere(self._get_success_rate_given_nearby(n0) == np.amax(self._get_success_rate_given_nearby(n0))))
            nearby_nodes = self.nearby_nodes[n0]
            # print("Node %d selected. Choosing %d (out of %d) nearby nodes." % (n0, num_nearby, len(nearby_nodes)))
            nearby_selected = [a for a in nearby_nodes if a in selected]
            # print("Nearby selected: ", str(nearby_selected))

            if len(nearby_selected) < num_nearby:
                nearby_dT = [(i, np.absolute(states[i].current_sensing - states[i].last_update)) for i in nearby_nodes if i not in selected ]
                dT = np.array([a[1] for a in nearby_dT])
                for i in range(num_nearby - len(nearby_selected)):
                    new_n = [a[0] for a in nearby_dT if a[1]==np.max(dT)][0]
                    selected.append(new_n)
                    action[new_n] = True
                    dT = np.delete(dT, np.argmax(dT))

            for a in nearby_nodes:
                if a not in selected:
                    selected.append(a)

        return action


    def _get_success_rate_given_nearby(self, node_idx):
        rate = np.zeros(len(self.num_packet_sent_given_nearby[node_idx]))
        for i in range(len(self.num_packet_sent_given_nearby[node_idx])):
            rate[i] = self.num_packet_sent_suc_given_nearby[node_idx][i] / float(self.num_packet_sent_given_nearby[node_idx][i])
        return rate


class Location:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return np.sqrt(dx * dx + dy * dy)

    @staticmethod
    def nearby_points(my_location, others, distance):
        count = 0
        for n in others:
            if my_location.distance(n) <= distance:
                count += 1
        return count

class NodeStates(enum.Enum):
    SENDING_NO_COLLISION = 1
    SENDING_COLLISION = 2
    SLEEPING = 4


class PacketInformation:
    def __init__(self, packet_id, node_id, payload, payload_size):
        self.packet_id = packet_id
        self.node_id = node_id
        self.payload_size = payload_size
        self.payload = payload
        self.snr = {}
        self.status = {}


class PacketStatus(enum.Enum):
    OK = 0
    NOT_LISTEN = 1
    WEAK_RSS = 2
    WEAK_SNR = 3
    COLLIDED = 4


class PacketRecord:
    def __init__(self, p, gateway, rss, snr, dispatch):
        self.node_id = p.node.id
        self.packet_id = p.id
        self.parameter = p.para
        self.timestamp = gateway.sim_env.now
        self.dispatch = dispatch
        self.status = PacketStatus.OK
        self.rss = rss
        self.snr = snr
        self.payload = p.payload
        self.transmission = p.transmission

    def __str__(self):
        return "Packet #{} from Node {} {}".format(self.packet_id, self.node_id, self.status)


class PerformanceAnimation:
    def __init__(self, node_location: list, gateway_location: list, performance: dict, step_size, fps=10):
        self.gateway_location = gateway_location
        self.x = list(n.x for n in node_location)
        self.y = list(n.y for n in node_location)
        self.step_size = step_size
        self.fps = fps
        self.info_fresh = performance["info_fresh"]
        self.success_rate = performance["success_rate"]
        assert self.info_fresh.shape[0] == self.success_rate.shape[0]
        self.frn = self.info_fresh.shape[0]
        writer = animation.writers['ffmpeg']
        self.writer = writer(fps=fps, metadata=dict(artist='Me'), bitrate=1800)

    def _update_plot(self, frame_number, ax1, ax2, time_label):
        ax1.clear()
        ax2.clear()
        ax1.set_title("Success rate")
        ax2.set_title(r"$\exp{-|dT|/10}}$")

        ax1.scatter3D(self.x, self.y, self.success_rate[frame_number, :], cmap="winter_r",
                      c=self.success_rate[frame_number, :], vmin=0, vmax=2)
        ax2.scatter3D(self.x, self.y, self.info_fresh[frame_number, :], cmap="winter_r",
                      c=self.info_fresh[frame_number, :], vmin=0, vmax=2)
        ax1.set_zlim(0, 1.1)
        ax2.set_zlim(0, 1.1)
        time_label.set_text(str(frame_number * self.step_size / 1000) + "s")

    def play(self):
        figure = plt.figure(0, figsize=(18, 9))
        ax1 = figure.add_subplot(1, 2, 1, projection='3d')
        ax2 = figure.add_subplot(1, 2, 2, projection='3d')
        textax = figure.add_axes([0.0, 0.95, 0.1, 0.05])
        textax.axis("off")
        time_label = textax.text(0.5, 0.5, "0s", ha="left", va="top")
        ax1.set_title("Success rate")
        ax2.set_title(r"$\exp{-|dT|/20}}$")
        ax1.scatter3D(self.x, self.y, self.success_rate[0, :], cmap="winter_r",
                      c=self.success_rate[0, :], vmin=0, vmax=2)
        ax2.scatter3D(self.x, self.y, self.info_fresh[0, :], cmap="winter_r",
                      c=self.info_fresh[0, :], vmin=0, vmax=2)
        ax1.set_zlim(0, 1.1)
        ax2.set_zlim(0, 1.1)
        animation.FuncAnimation(figure, self._update_plot, self.frn, fargs=(ax1, ax2, time_label),
                                interval=2000 / self.fps)
        plt.figure(0)
        plt.show()

    def save(self, title):
        figure = plt.figure( figsize=(18, 9))
        ax1 = figure.add_subplot(1, 2, 1, projection='3d')
        ax2 = figure.add_subplot(1, 2, 2, projection='3d')
        ax_text = figure.add_axes([0.0, 0.95, 0.1, 0.05])
        ax_text.axis("off")
        time_label = ax_text.text(0.5, 0.5, "0s", ha="left", va="top")
        ax1.set_title("Success rate")
        ax2.set_title(r"$\exp{-|dT|/20}}$")
        ax1.scatter3D(self.x, self.y, self.success_rate[0, :], cmap="winter_r",
                      c=self.success_rate[0, :], vmin=0, vmax=2)
        ax2.scatter3D(self.x, self.y, self.info_fresh[0, :], cmap="winter_r",
                      c=self.info_fresh[0, :], vmin=0, vmax=2)
        ax1.set_zlim(0, 1.1)
        ax2.set_zlim(0, 1.1)
        ani = animation.FuncAnimation(figure, self._update_plot, self.frn, fargs=(ax1, ax2, time_label),
                                      interval=2000 / self.fps)
        ani.save(title, writer=self.writer)

def T_threshold_policy(T_threshold, simulation):
    action = []
    states = simulation.node_states("current_sensing")
    for s in states:
        if s.current_sensing > T_threshold:
            action.append(True)
        else:
            action.append(False)
    return action


def Tdiff_threshold_policy(T_threshold, simulation):
    action = []
    states = simulation.node_states("current_sensing", "last_update")
    for s in states:
        if np.absolute(s.current_sensing - s.last_update) > T_threshold:
            action.append(True)
        else:
            action.append(False)
    return action


def random_policy(percentage, simulation, fixed_number=False):
    return np.random.choice([True, False], len(simulation.nodes), p=[percentage, 1-percentage])

def print_statistics(simulation, num_steps):
    statistics = simulation.node_states("num_total_packets_sent", "num_unique_packets_received", "total_transmit_time",
                                        "total_energy_usage")
    print('Of ', len(simulation.nodes), ' nodes:')
    print("Numbers of packets sent:")
    print([s.num_total_packets_sent for s in statistics])
    print("Numbers of packets successfully received:")
    print([s.num_unique_packets_received for s in statistics])
    print("Total transmission time: (s)")
    print([s.total_transmit_time / 1000.0 for s in statistics])
    print("Total energy consumption: (J)")
    print([s.total_energy_usage / 1000.0 for s in statistics])
    print('')

    tol_sent = sum([s.num_total_packets_sent for s in statistics])
    tol_receive = sum([s.num_unique_packets_received for s in statistics])
    ave_e = np.average([s.total_energy_usage / 1000.0 for s in statistics])
    max_e = np.max([s.total_energy_usage / 1000.0 for s in statistics])
    print("Total number of packets sent: ", tol_sent)
    print("Total number of packets successfully received: ", tol_receive)
    print("Average duty circle: ",
          np.average([s.total_transmit_time / 1000.0 for s in statistics]) / (num_steps * simulation.step_time) * 100, "%")
    print("Average energy consumption: {:.2f}(mJ), {:.6f}% ".format(ave_e, ave_e / BATTERY_ENERGY * 100))
    print("Maximum energy consumption: {:.2f}(mJ), {:.6f}%".format(max_e, max_e / BATTERY_ENERGY * 100))
    print("Success ratio: {:.2f}%".format(tol_receive * 100.0 / tol_sent))
