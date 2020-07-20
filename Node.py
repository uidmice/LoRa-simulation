import numpy as np
from enum import Enum, auto
import math

from LoRaParameters import LoRaParameters
from Gateway import Gateway, DownlinkPacket
from TransmissionInterface import AirInterface
from config import *

class NodeState(Enum):
    SLEEP = auto()
    TX = auto()
    RX = auto()

class Node():
    def __init__(self, nodeid, energy_profile, lora_para:LoRaParameters, x, y,
        base_stations,  payload_size, air_interface:AirInterface, sim_env ):
        self.id = nodeid
        self.para = lora_para
        self.x = x
        self.y = y
        print('node %d' %nodeid, "  @  (", self.x, ",", self.y,")", "ch: ", self.para.channel, "sf: ", self.para.sf)
        self.gain = 1
        self.energy_profile = energy_profile
        self.base_stations = base_stations
        self.current_state = NodeState.SLEEP
        self.payload_size = payload_size
        self.air_interface = air_interface
        self.unique_packet_id = 0
        self.num_unique_packets_sent = 0
        self.num_packets_sent = 0
        self.packet_to_send = None
        self.sim_env = sim_env

    def run(self):
        while True:
            # added also a random wait to accommodate for any timing issues on the node itself
            random_wait = np.random.randint(0,  1000)
            yield self.sim_env.timeout(random_wait)

            # ------------SENDING------------ #
            if np.random.random() < 0.1:
                self.unique_packet_id += 1
                packet = UplinkPacket(node=self, id=self.unique_packet_id)
                print(self.sim_env.now, ": ",  str(packet), " SENDING")
                self.packet_to_send = packet
                lost = yield self.sim_env.process(self.send(packet))
                if lost:
                    lost = yield self.sim_env.process(self.message_lost())
                if not lost:
                    print(self.sim_env.now, ": ",  str(packet), " DONE")
                    self.num_unique_packets_sent += 1  # at the end to be sure that this packet was tx
            yield self.sim_env.timeout(600000)

    def send(self, packet):
        self.current_state = NodeState.TX
        packet.send(self.sim_env.now)
        yield self.sim_env.timeout(int(np.ceil(packet.time_on_air)))
        collided = self.air_interface.collision(packet)
        lost = collided
        if not collided:
            for bs in packet.collided:
                if not packet.collided[bs]:
                    self.base_stations[bs].receive_packet(packet)
            if not any(packet.received.values()):
                lost = True
        self.current_state = NodeState.RX
        yield self.sim_env.timeout(DLtime)
        self.current_state = NodeState.SLEEP
        return lost

    def message_lost(self):
        packet = self.packet_to_send
        packet.lost_cnt += 1
        if packet.lost_cnt < MAX_RETRY:
            random_wait = np.random.randint(0,  1000*(2**packet.lost_cnt))
            yield self.sim_env.timeout(random_wait)
            print(self.sim_env.now, ": ",  str(packet), " RESENDING")
            lost = yield self.sim_env.process(self.send(packet))
            if lost:
                lost = yield self.sim_env.process(self.message_lost())
                return lost
        else:
            print(self.sim_env.now, ": ",  str(packet), " FIELD; reach maximum retries.")
            return True

    def __str__(self):
        return "Node {}".format(self.id)

class EnergyProfile:
    rx_power_mA = [10.3, 11.1, 12.6]

    # Transmit consumption in mA from -2 to +17 dBm
    tx_power_mA = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
          24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
          82, 85, 90,                                          # PA_BOOST/PA1: 15..17
          105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
    tx_power_cof_k = 0.6
    tx_power_cof_b = 17
    def __init__(self, proc_power, Vdd = 3.3,  E_tot = 22572000):
        self.proc_power_mW = proc_power
        self.Vdd = Vdd
        self.E_tot = E_tot

    def get_E_compute(self, t):
        return self.proc_power_mW * t

    def get_E_transmit(self, tp_dbm, t):
        # return (10**(tp_dbm/10.0) * tx_power_cof_k + tx_power_cof_b) *  self.Vdd * t
        return EnergyProfile.tx_power_mA[range(-2,21).index(tp_dbm)]*  self.Vdd * t

    def get_E_receive (self, bw, t):
        return EnergyProfile.rx_power_mA[[125,250,500].index(bw)] * self.Vdd * t


def time_on_air(sf, bw, cr,  h, de, pl):
    Npream = 8   # number of preamble symbol (12.25  from Utz paper)
    Tsym = (2.0**sf)/bw  # msec
    Tpream = (Npream + 4.25)*Tsym
    payloadSymbNB = 8 + max(
            math.ceil(
                (
                        8.0 * pl - 4.0 *sf + 28  - 20 * h) / (
                        4.0 * (sf - 2 *de)))
            * (cr + 4), 0)
    Tpayload = payloadSymbNB * Tsym
    return Tpream + Tpayload # msec

class UplinkPacket():
    def __init__(self, node: Node,  id):
        self.id = id
        self.node = node
        self.para = node.para
        self.payload_size = node.payload_size
        self.overlapped_packets = []
        self.received = {}
        self.collided = {}
        self.rss = {}
        self.snr = {}
        self.start_at = None
        self.end_at = None
        self.time_on_air = None
        self.lost_cnt = 0
        self.transmissionInterface = node.air_interface

    def airtime(self): #in ms
        if self.time_on_air is None:
            self.time_on_air = time_on_air(self.para.sf, self.para.bw, self.para.cr,self.para.h,self.para.de, self.payload_size )
        return self.time_on_air

    def change_freq_to(self, freq):
        self.para.change_freq_to(freq)

    def change_channel_to(self, channel):
        self.para.change_channel_to(channel)

    def change_sf_to(self, sf):
        self.para.change_sf_to(sf)

    def change_tp_to(self, tp):
        self.para.change_tp_to(tp)

    def send(self, t):
        self.start_at = t
        self.end_at = self.start_at + self.airtime()
        self.node.num_packets_sent += 1
        for b in self.node.base_stations:
            dist = np.sqrt((self.node.x-b.x)**2+(self.node.y-b.y)**2)
            self.rss[b.id] = self.transmissionInterface.prop_model.tp_to_rss(False, self.para.tp, dist)
            self.snr[b.id] =self.transmissionInterface.snr_model.rss_to_snr(self.rss[b.id])
            self.received[b.id] = False
            self.collided[b.id] = False
        self.transmissionInterface.register(self)

    def __str__(self):
        return "Packet #{} from Node {}".format(self.id, self.node.id)
