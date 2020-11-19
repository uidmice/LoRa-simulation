import simpy
import numpy as np

from framework.utils import Location
from framework.Node import Node, EnergyProfile
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface
from framework.Backend import Server, Application
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
            assert False, "%s environment is not implemented" %(environment)
        self.sim_env.process(self.environment.update(UPDATA_RATE))
        self.server = Server(self.gateways, self.sim_env, Application())
        self.air_interface = AirInterface(self.sim_env, self.gateways, self.server)
        for i in range(len(nodes_positions)):
            node = Node(i, EnergyProfile(0.1), LoRaParameters(i % Gateway.NO_CHANNELS, sf=12),
                                   self.air_interface, self.sim_env, nodes_positions[i], True)
            node.last_payload_sent = self.environment.sense(nodes_positions[i])
            self.nodes.append(node)
        for i in range(len(gateway_positions)):
            self.gateways.append(Gateway(i, gateway_positions[i], self.sim_env))

    def node_states(self, *args, **kwargs):
        return list(a.get_status(*args, **kwargs) for a in self.nodes)

    def step(self, actions):
        assert len(self.nodes) == len(actions)
        assert self.sim_env.now == self.steps * self.step_time
        self.steps += 1
        send_index = [idx for idx, send in enumerate(actions) if send]
        for i in range(len(self.nodes)):
            self.sim_env.process(self._node_send_sensed_value(i, actions[i]))
        self.sim_env.run(self.step_time * self.steps)
        reward = 0
        received = 0
        for i in send_index:
            if self.nodes[i].packet_to_send.received:
                received += 1
                if self.nodes[i].last_payload_change:
                    reward += np.exp(-20/np.absolute(self.nodes[i].last_payload_change))
        return reward, 1 - received/(len(send_index)*1.0)

    def _node_send_sensed_value(self, node_index, send):
        yield self.sim_env.timeout(np.random.randint(self.offset))
        node = self.nodes[node_index]
        value = node.sense(self.environment)
        if send:
            packet = node.create_unique_packet(value, True, True)
            yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def _node_send_test(self, node_index):
        yield self.sim_env.timeout(np.random.randint(self.offset))
        node = self.nodes[node_index]
        packet = node.create_unique_packet(0, True, True)
        yield self.sim_env.process(node.send(packet))
        yield self.sim_env.timeout(self.step_time * self.steps - self.sim_env.now)

    def pre_adr(self, rounds: int, show=False):
        assert rounds > 100
        per = np.zeros((len(self.nodes), rounds))
        for i in range(len(self.nodes)):
            self.nodes[i].adr = True

        for i in range(rounds):
            assert self.sim_env.now == self.steps * self.step_time
            self.steps += 1
            for j in range(len(self.nodes)):
                self.sim_env.process(self._node_send_test(j))
            self.sim_env.run(self.step_time * self.steps)
            for j in range(len(self.nodes)):
                per[j, i] = self.nodes[j].moving_average_per()
        if show:
            plt.figure(figsize=(5,5))
            plt.plot(np.mean(per, axis=0))
            plt.title("Running ADR...")
            plt.xlabel("iterations")
            plt.ylabel("Packet error rate")
        return per

    def reset(self):
        self.sim_env = simpy.Environment()
        self.steps = 0
        self.environment.reset(self.sim_env)
        self.sim_env.process(self.environment.update(UPDATA_RATE))
        for i in range(len(self.nodes)):
            self.nodes[i].reset(self.sim_env)
        for i in range(len(self.gateways)):
            self.gateways[i].reset(self.sim_env)
        self.server.reset(self.sim_env)
        self.air_interface.reset(self.sim_env)