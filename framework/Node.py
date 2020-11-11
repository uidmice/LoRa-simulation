import math
import numpy as np
import enum
import simpy

from config import *
from .TransmissionInterface import AirInterface
from .LoRaParameters import LoRaParameters


class NodeStates(enum.Enum):
    SENDING_NO_COLLISION = 1
    SENDING_COLLISION = 2
    SLEEPING = 4


class NodeStatus:
    def __init__(self, node_id):
        self.node_id = node_id
        self.state = NodeStates.SLEEPING

        self.unique_packet_id = 0  # unique packets not counting for multiple tries
        self.unique_packet_sent = []  # unique packets sent successfully received
        self.num_packets_sent = 0  # total number of packets sent

        self.transmit_time = {}
        self.receive_time = {}
        self.success_rate_history = {}
        self.sensed_history = {}


class Node:
    def __init__(self, node_id, energy_profile, lora_para: LoRaParameters, x, y,
                 air_interface: AirInterface, sim_env, status: NodeStatus, adr,
                 adr_ack_limit=10, adr_ack_delay=5):
        self.id = node_id
        self.para = lora_para
        self.x = x
        self.y = y
        if DEBUG:
            print('node %d' % node_id, "  @  (", self.x, ",", self.y, ")", ", ch = ", self.para.channel, ", sf = ",
                  self.para.sf, ", tp = ", self.para.tp)
        self.energy_profile = energy_profile
        self.payload_size = 10
        self.air_interface = air_interface
        self.sim_env = sim_env
        self.status = status
        self.adr = adr
        self.packet_to_send = None

        if adr:
            self.adr_ack_limit = adr_ack_limit
            self.adr_ack_delay = adr_ack_delay
            self.adr_ack_cnt = 0

    def __str__(self):
        return "Node {}".format(self.id)

    # def run(self, time = 1000, threshold = 45):
    # while not time:
    #     yield self.sim_env.timeout(np.random.randint(10000))
    #
    #     # ------------SENDING------------ #
    #     phys_sense = 50
    #     if self.external:
    #         phys_sense = self.external.sense(self.x, self.y)
    #     if phys_sense > threshold:
    #         self.unique_packet_id += 1
    #         adr_req = self.adr_ack_cnt>= self.adr_ack_limit
    #         packet = UplinkPacket(node=self, payload = phys_sense, id=self.unique_packet_id, adrAckReq = adr_req)
    #         if DEBUG:
    #             print(self.sim_env.now, ": ",  str(packet), " SENDING")
    #         self.packet_to_send = packet
    #         lost = yield self.sim_env.process(self.send(packet))
    #         if lost:
    #             lost = yield self.sim_env.process(self.message_lost())
    #         if not lost:
    #             if DEBUG:
    #                 print(self.sim_env.now, ": ",  str(packet), " DONE")
    #             self.num_unique_packets_sent += 1  # at the end to be sure that this packet was tx
    #         self.status[self.id] = 0

    # while True:
    #     random_wait = np.random.randint(time/2)
    #     yield self.sim_env.timeout(random_wait)
    #
    #     # ------------SENDING------------ #
    #     phys_sense = 50
    #     if self.external:
    #         phys_sense = self.external.sense(self.x, self.y)
    #     if phys_sense > threshold:
    #         self.unique_packet_id += 1
    #         packet = UplinkPacket(node=self, payload = phys_sense, id=self.unique_packet_id, adrAckReq = False)
    #         if DEBUG:
    #             print(self.sim_env.now, ": ",  str(packet), " SENDING")
    #         self.packet_to_send = packet
    #         lost = yield self.sim_env.process(self.send(packet))
    #         if not lost:
    #             if DEBUG:
    #                 print(self.sim_env.now, ": ",  str(packet), " DONE")
    #             self.num_unique_packets_sent += 1  # at the end to be sure that this packet was tx
    #             self.last_payload = phys_sense
    #     self.success_history.append(self.success_rate())
    #     self.true_history.append(phys_sense)
    #     if self.last_payload:
    #         self.value_history.append(self.last_payload)
    #     else:
    #         self.value_history.append(0)
    #     now = self.sim_env.now
    #     now = now % time
    #     yield self.sim_env.timeout(time - now)

    # while True:
    #     random_wait = np.random.randint(time/2)
    #     yield self.sim_env.timeout(random_wait)
    #
    #     # ------------SENDING------------ #
    #     phys_sense = 50
    #     if self.external:
    #         phys_sense = self.external.sense(self.x, self.y)
    #     if not self.last_payload:
    #         self.last_payload = 0
    #     diff = np.absolute(self.last_payload - phys_sense)
    #     if diff > threshold:
    #         self.unique_packet_id += 1
    #         packet = UplinkPacket(node=self, payload = phys_sense, id=self.unique_packet_id, adrAckReq = False)
    #         if DEBUG:
    #             print(self.sim_env.now, ": ",  str(packet), " SENDING")
    #         self.packet_to_send = packet
    #         lost = yield self.sim_env.process(self.send(packet))
    #         if not lost:
    #             if DEBUG:
    #                 print(self.sim_env.now, ": ",  str(packet), " DONE")
    #             self.num_unique_packets_sent += 1  # at the end to be sure that this packet was tx
    #             self.last_payload = phys_sense
    #     self.success_history.append(self.success_rate())
    #     self.true_history.append(phys_sense)
    #     if self.last_payload:
    #         self.value_history.append(self.last_payload)
    #     else:
    #         self.value_history.append(0)
    #     now = self.sim_env.now
    #     now = now % time
    #     yield self.sim_env.timeout(time - now)

    def send(self, packet):
        self.packet_to_send = packet
        self.status.num_packets_sent += 1
        self.status.state = NodeStates.SENDING_NO_COLLISION
        yield self.sim_env.process(packet.schedule())

        # not accounting energy cost to run on-device algorithm
        self.energy_profile.E_tot -= self.energy_profile.transmit_energy_cost(packet.para.tp, packet.time_on_air)
        self.status.transmit_time[self.sim_env.now] = packet.time_on_air
        yield packet.receive
        if packet.received:
            self.status.unique_packet_sent.append(packet.id)
        if self.adr:
            self.ed_adr()
        self.status.state = NodeStates.SLEEPING


    def ed_adr(self):
        self.adr_ack_cnt += 1
        if DEBUG:
            print("ADR_ACK_CNT = ", self.adr_ack_cnt)
        if self.packet_to_send.dl:
            if DEBUG:
                print("Downlink Received. ADR_ACK_CNT cleared.")
            self.adr_ack_cnt = 0
            if self.packet_to_send.dl.adr_para:
                self.para.sf = self.packet_to_send.dl.adr_para['sf']
                self.para.tp = self.packet_to_send.dl.adr_para['tp']
                if DEBUG:
                    print("=============== ADR update ===============")
                    print("ADR Received with sf = {}, tp = {}".format(self.para.sf, self.para.tp))
            return
        sf = self.para.sf
        tp = self.para.tp
        if self.adr_ack_cnt >= self.adr_ack_limit:
            if sf >= max(LoRaParameters.SPREADING_FACTORS) and tp >= max(LoRaParameters.TP_DBM):
                self.para.sf = max(LoRaParameters.SPREADING_FACTORS)
                self.para.tp = max(LoRaParameters.TP_DBM)
                self.adr_ack_cnt = 0
                if DEBUG:
                    print("ADR improvement not possible. ADR_ACK_CNT cleared.")
                return

            if self.adr_ack_cnt == self.adr_ack_limit + self.adr_ack_delay:
                if tp < max(LoRaParameters.TP_DBM):
                    self.para.tp += 3
                else:
                    self.para.sf += 1
                self.adr_ack_cnt = self.adr_ack_limit
                if DEBUG:
                    print("=============== ADR update ===============")
                    print("ED ADR: sf = {}, tp = {}".format(self.para.sf, self.para.tp))
        return

    def success_rate(self):
        if self.status.unique_packet_id == 0:
            return 0
        return len(self.status.unique_packet_sent) / float(self.status.unique_packet_id)

    def sense(self, external):
        value = external.sense(self.x, self.y)
        packet = UplinkPacket(self, payload=value)
        return packet

class EnergyProfile:
    rx_power_mA = [10.3, 11.1, 12.6]

    # Transmit consumption in mA from -2 to +17 dBm
    tx_power_mA = [22, 22, 22, 23,  # RFO/PA0: -2..1
                   24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
                   82, 85, 90,  # PA_BOOST/PA1: 15..17
                   105, 115, 125, 135]  # PA_BOOST/PA1+PA2: 18..20

    def __init__(self, proc_power, Vdd=3.3, E_tot=BATTERY_ENERGY):
        self.proc_power_mW = proc_power
        self.Vdd = Vdd
        self.origin_E_tot = E_tot
        self.E_tot = E_tot

    def compute_energy_cost(self, t):
        return self.proc_power_mW * t / 1000

    def transmit_energy_cost(self, tp_dbm, t):
        # return (10**(tp_dbm/10.0) * tx_power_cof_k + tx_power_cof_b) *  self.Vdd * t
        return EnergyProfile.tx_power_mA[range(-2, 22).index(tp_dbm)] * self.Vdd * t / 1000

    def receive_energy_cost(self, bw, t):
        return EnergyProfile.rx_power_mA[[125, 250, 500].index(bw)] * self.Vdd * t / 1000


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


class UplinkPacket():
    def __init__(self, node: Node, payload=0, adr=True, adrAckReq=False):
        self.id = node.status.unique_packet_id
        node.status.unique_packet_id += 1
        self.node = node
        self.para = node.para
        self.payload = payload
        self.payload_size = node.payload_size
        self.start_at = None
        self.end_at = None
        self.time_on_air = None
        self.lost_cnt = 0
        self.received = False
        self.adr = adr
        self.adrAckReq = adrAckReq
        self.air_interface = node.air_interface

        self.transmission = None
        self.dl = None
        self.receive = None

    def airtime(self):  # in ms
        print("Calculating airtime")
        if self.time_on_air is None:
            self.time_on_air = airtime(self.para.sf, self.para.bw, self.para.cr, self.para.h, self.para.de,
                                           self.payload_size)
        return self.time_on_air

    def change_freq_to(self, freq):
        self.para.change_freq_to(freq)

    def change_channel_to(self, channel):
        self.para.change_channel_to(channel)

    def change_sf_to(self, sf):
        self.para.change_sf_to(sf)

    def change_tp_to(self, tp):
        self.para.change_tp_to(tp)

    def schedule(self, t=0):
        assert t >= 0
        self.start_at = t + self.node.sim_env.now
        self.end_at = self.start_at + self.airtime()
        self.node.status.num_packets_sent += 1
        if t > 0:
            yield self.node.sim_env.timeout(t)
        self.transmission = self.node.sim_env.process(self.send())
        yield self.transmission

    def send(self):
        print(str(self.node.sim_env.now) + ": "+str(self) + " is being sent\t TOA: "+ str(self.time_on_air) + " ms")
        self.air_interface.transmit(self)
        self.receive = self.node.sim_env.event()
        yield self.node.sim_env.timeout(self.time_on_air)


    def __str__(self):
        return "Packet #{} from Node {}".format(self.id, self.node.id)
