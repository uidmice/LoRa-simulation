import gc
import random
import numpy as np

from Gateway import Gateway
from Node import Node, UplinkPacket

class PropagationModel:
    # http://ieeexplore.ieee.org.kuleuven.ezproxy.kuleuven.be/stamp/stamp.jsp?tp=&arnumber=7377400
    def __init__(self, gamma=2.32, d0=1000.0, std=7.8, Lpld0=128.95, GL=0):
        self.gamma = gamma
        self.d0 = d0
        self.std = std
        if self.std<0:
            self.std = 0
        self.Lpld0 = Lpld0
        self.GL = GL

    def tp_to_rss(self, indoor: bool, tp_dBm: int, d: float):
        bpl = 0  # building path loss
        if indoor:
            bpl = np.random.choice([17, 27, 21, 30])  # according Rep. ITU-R P.2346-0
        Lpl = 10 * self.gamma * np.log10(d / self.d0) + np.random.normal(self.Lpld0, self.std) + bpl
        if Lpl <0:
            Lpl = 0
        return tp_dBm - self.GL - Lpl


class SNRModel:
    def __init__(self):
        self.noise = -80  # mean_mean_values
        self.std_noise = 6  # mean_std_values
        self.noise_floor = -174 + 10 * np.log10(125e3)

    def rss_to_snr(self, rss: float):
        return rss - self.noise_floor

class AirInterface:
    def __init__(self, prop_model = None, snr_model = None):
        self.prop_model = prop_model
        self.snr_model = snr_model
        self.packet_in_air = []
        if self.prop_model==None:
            self.prop_model = PropagationModel()
        if self.snr_model == None:
            self.snr_model = SNRModel()


    @staticmethod
    def frequency_collision(p1: UplinkPacket, p2: UplinkPacket):
        """frequencyCollision, conditions
                |f1-f2| <= 120 kHz if f1 or f2 has bw 500
                |f1-f2| <= 60 kHz if f1 or f2 has bw 250
                |f1-f2| <= 30 kHz if f1 or f2 has bw 125
        """

        p1_freq = p1.para.freq
        p2_freq = p2.para.freq

        p1_bw = p1.para.bw
        p2_bw = p2.para.bw

        if abs(p1_freq - p2_freq) <= 120000 and (p1_bw == 500 or p2_bw == 500):
            print("frequency coll 500")
            return True
        elif abs(p1_freq - p2_freq) <= 60000 and (p1_bw == 250 or p2_bw == 250):
            print("frequency coll 250")
            return True
        elif abs(p1_freq - p2_freq) <= 30000 and (p1_bw == 125 or p2_bw == 125):
            print("frequency coll 125")
            return True

        print("no frequency coll")
        return False

    @staticmethod
    def sf_collision(p1: UplinkPacket, p2: UplinkPacket):
        if p1.para.sf == p2.para.sf:
            print("collision sf node {} and node {}".format(p1.node.id, p2.node.id))
            return True
        print("no sf collision")
        return False

    def register(self, p: UplinkPacket):
        self.packet_in_air.append(p)
        for packet in self.packet_in_air:
            if not ((p.start_at > packet.end_at) or (p.end_at<packet.start_at)):
                p.overlapped_packets.append(packet)
                packet.overlapped_packets.append(p)
        self.packet_in_air.sort(key = lambda x: x.start_at)

    # @staticmethod
    # def power_collision(me: UplinkPacket, other: UplinkPacket, time_collided_nodes):
    #     power_threshold = 6  # dB
    #     print("pwr: node {0.node.id} {0.rss:3.2f} dBm node {1.node.id} {1.rss:3.2f} dBm; diff {2:3.2f} dBm"
    #             .format(me, other, round(me.rss - other.rss, 2) ) )
    #     if abs(me.rss - other.rss) < power_threshold:
    #         print("collision pwr both node {} and node {} (too close to each other)"
    #             .format(me.node.id, other.node.id))
    #         if me in time_collided_nodes:
    #             me.collided = True
    #         if other in time_collided_nodes:
    #             other.collided = True
    #
    #     elif me.rss - other.rss < power_threshold:
    #         # me has been overpowered by other
    #         # me will collided if also time_collided
    #
    #         if me in time_collided_nodes:
    #             print("collision pwr both node {} has collided by node {}".format(me.node.id, other.node.id))
    #             me.collided = True
    #     else:
    #         if other in time_collided_nodes:
    #             print("collision pwr both node {} has collided by node {}".format(other.node.id, me.node.id))
    #             other.collided = True
    #
    # def collision(self, packet: UplinkPacket) -> bool:
    #     print("CHECK node {} (sf:{} bw:{} channel:{}) #others: {}".format(
    #             packet.node.id, packet.para.sf, packet.para.bw, packet.para.channel,
    #             len(self.packages_in_air)))
    #     if packet.collided:
    #         return True
    #     for other in self.packages_in_air:
    #         if other.node.id != packet.node.id:
    #             print(">> node {} (sf:{} bw:{} channel:{})".format(
    #                     other.node.id, other.para.sf, other.para.bw,
    #                     other.para.channel))
    #             if AirInterface.frequency_collision(packet, other):
    #                 if AirInterface.sf_collision(packet, other):
    #                     time_collided_nodes = AirInterface.timing_collision(packet, other)
    #                     if time_collided_nodes is not None:
    #                         AirInterface.power_collision(packet, other, time_collided_nodes)
    #     return packet.collided
