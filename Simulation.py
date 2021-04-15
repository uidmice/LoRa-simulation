import simpy
import random
from collections import deque

from framework.utils import Location
from framework.Node import Node, EnergyProfile
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface
from framework.Backend import Server, Application
from framework.LoRaParameters import LoRaParameters
from framework.Environment import *
import os.path
import pickle

class Simulation:
    ENVIRONMENT_TYPE = ["temp"]

    def __init__(self, nodes_positions, gateway_positions, step_time, connection, config_name, environment="temp", offset=2000):
        self.nodes = []
        self.gateways = []
        assert step_time >= offset + 3000
        self.step_time = step_time
        self.offset = offset
        self.steps = 0
        self.config_name = config_name
        self.sim_env = simpy.Environment()
        assert environment in Simulation.ENVIRONMENT_TYPE
        if environment == "temp":
            self.environment = TempEnvironment(self.sim_env, Location(MAX_DISTANCE, -MAX_DISTANCE),
                                               Location(-MAX_DISTANCE, MAX_DISTANCE), 296.15, dx=GRID)
        else:
            assert False, "%s environment is not implemented" %(environment)
        self.sim_env.process(self.environment.update(UPDATA_RATE))
        link = []
        for loc in connection:
            for l2 in connection[loc]:
                link.append([nodes_positions.index(loc), nodes_positions.index(l2)])
        self.app = Application(list(range(len(nodes_positions))), link)
        self.server = Server(self.gateways, self.sim_env, self.app)
        self.air_interface = AirInterface(self.sim_env, self.gateways, self.server)
        config_file = './config/'+config_name+'_lora.pickle'
        lora_para_exist = False
        if os.path.exists(config_file):
            lora_para = pickle.load(open(config_file, 'rb'))
            lora_para_exist = True
        else:
            lora_para = [ LoRaParameters(i % Gateway.NO_CHANNELS, sf=12) for i in range(len(nodes_positions))]
        for i in range(len(nodes_positions)):
            node = Node(i, EnergyProfile(0.1), lora_para[i],
                                   self.air_interface, self.sim_env, nodes_positions[i], True)
            node.last_payload_sent = self.environment.sense(nodes_positions[i])
            self.nodes.append(node)
        for i in range(len(gateway_positions)):
            self.gateways.append(Gateway(i, gateway_positions[i], self.sim_env))

        self.constructed_field = None

        if not lora_para_exist:
            print("Start generating new lora configuration file for " + config_name)
            self.pre_adr(1000, True, percentage=0.6)
            pickle.dump([n.para for n in self.nodes], open(config_file, 'wb'))
            self.reset()



    def node_states(self, *args, **kwargs):
        return list(a.get_status(*args, **kwargs) for a in self.nodes)

    def step(self, actions):
        assert len(self.nodes) == len(actions)
        assert self.sim_env.now == self.steps * self.step_time
        self.constructed_field = self.field_reconstruction()
        self.steps += 1
        send_index = [idx for idx, send in enumerate(actions) if send]
        for i in range(len(self.nodes)):
            self.sim_env.process(self._node_send_sensed_value(i, actions[i]))
        self.sim_env.run(self.step_time * self.steps)
        received = []
        for i in send_index:
            if self.nodes[i].packet_to_send.received:
                received.append(i)
                # if self.nodes[i].last_payload_change:
                #     reward += np.exp(-20/np.absolute(self.nodes[i].last_payload_change))
        return send_index, received

    def _node_send_sensed_value(self, node_index, send):
        node = self.nodes[node_index]
        value = node.sense(self.environment)
        time = self.sim_env.now
        yield self.sim_env.timeout(np.random.randint(self.offset))

        if send:
            packet = node.create_unique_packet({'value':value, 'time': time}, True, True)
            yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def _node_send_test(self, node_index):
        yield self.sim_env.timeout(np.random.randint(self.offset))
        node = self.nodes[node_index]
        packet = node.create_unique_packet(None, True, True)
        yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def pre_adr(self, rounds: int, show=False, percentage=0.8):
        assert rounds > 50
        N = int(percentage*len(self.nodes))
        for i in range(len(self.nodes)):
            self.nodes[i].adr = True

        record_per = []
        record_std = []
        for i in range(rounds):
            assert self.sim_env.now == self.steps * self.step_time
            self.steps += 1
            send_node = random.sample(range(len(self.nodes)), N )
            for j in send_node:
                self.sim_env.process(self._node_send_test(j))
            self.sim_env.run(self.step_time * self.steps)
            per = np.zeros(N)
            for j, idx in enumerate(send_node):
                per[j] = self.nodes[idx].moving_average_per()
            record_per.append(np.mean(per))
            record_std.append(np.std(per))
        latest_per = record_per[-50:]
        latest_std = record_std[-50:]

        count = 0
        threshold = 0.05
        while not self._check_adr_convergence(latest_per, threshold):
            for i in range(50):
                assert self.sim_env.now == self.steps * self.step_time
                self.steps += 1
                send_node = random.sample(range(len(self.nodes)), N)
                for j in send_node:
                    self.sim_env.process(self._node_send_test(j))
                self.sim_env.run(self.step_time * self.steps)
                per = np.zeros(N)
                for j, idx in enumerate(send_node):
                    per[j] = self.nodes[idx].moving_average_per()
                latest_per[i] = np.mean(per)
                latest_std[i] = np.std(per)
            count += 1
            if count == int(10/percentage) or count == 10:
                self.reset(True)
                plt.figure(figsize=(5, 5))
                plt.errorbar(range(len(record_per)), record_per, yerr=record_std, errorevery=int(len(record_per) / 25))
                plt.title("Running ADR...")
                plt.xlabel("iterations")
                plt.ylabel("Packet error rate")
                plt.show()
                return self.pre_adr(rounds, show, percentage)
            record_per.extend(latest_per)
            record_std.extend(latest_std)
        if np.average(record_per[-50:-1]) > 0.6:
            self.reset(True)
            plt.figure(figsize=(5, 5))
            plt.errorbar(range(len(record_per)), record_per, yerr=record_std, errorevery=int(len(record_per) / 25))
            plt.title("Running ADR...")
            plt.xlabel("iterations")
            plt.ylabel("Packet error rate")
            plt.show()
            return self.pre_adr(rounds, show, percentage)
        if show:
            plt.figure(figsize=(5,5))
            plt.errorbar(range(len(record_per)), record_per, yerr=record_std, errorevery=int(len(record_per)/25))
            plt.title("Running ADR...")
            plt.xlabel("iterations")
            plt.ylabel("Packet error rate")
        return record_per, record_std

    def reset(self, reset_lora=False):
        self.sim_env = simpy.Environment()
        self.steps = 0
        self.environment.reset(self.sim_env)
        self.sim_env.process(self.environment.update(UPDATA_RATE))
        for i in range(len(self.nodes)):
            self.nodes[i].reset(self.sim_env)
            self.nodes[i].last_payload_sent = self.environment.sense(self.nodes[i].location)
            if reset_lora:
                self.nodes[i].para = LoRaParameters(i % Gateway.NO_CHANNELS, sf=12)
        for i in range(len(self.gateways)):
            self.gateways[i].reset(self.sim_env)
        self.server.reset(self.sim_env)
        self.air_interface.reset(self.sim_env)

    def _check_adr_convergence(self, mean, difference):
        return np.max(mean) - np.min(mean) < difference

    def field_reconstruction(self):
        return self.app.fusion_center.field_reconstruct(self.step_time * (self.steps))

    def eval_positive(self):
        diff = np.array([n.latest_sensed for n in self.nodes]) - np.fromiter(self.constructed_field.values(), dtype=float)
        return diff