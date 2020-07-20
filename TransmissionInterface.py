import gc
import random
import numpy as np
import simpy

from Gateway import Gateway
from LoRaParameters import LoRaParameters

class PropagationModel:
    #log distance path loss model (or log normal shadowing)
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
    def __init__(self, sim_env, prop_model = None, snr_model = None):
        self.prop_model = prop_model
        self.snr_model = snr_model
        self.packets_in_air = {}
        self.sems = {}
        for i in range(len(LoRaParameters.CHANNELS)):
            self.packets_in_air[i] = []
            self.sems[i] = simpy.Resource(sim_env, capacity=1)
        if self.prop_model==None:
            self.prop_model = PropagationModel()
        if self.snr_model == None:
            self.snr_model = SNRModel()


    @staticmethod
    def sf_collision(p1, p2):
        if p1.para.sf == p2.para.sf:
            return True
        return False

    def register(self, p):
        ch = p.para.channel
        with self.sems[ch].request() as req:
            for packet in self.packets_in_air[ch]: #same frequency
                if not ((p.start_at > packet.end_at) or (p.end_at<packet.start_at)): #time overlap
                    if AirInterface.sf_collision(p, packet): # sf collision
                        p.overlapped_packets.append(packet)
                        packet.overlapped_packets.append(p)
            self.packets_in_air[ch].append(p)

    def collision(self, packet):
        threshold = 6
        ch = packet.para.channel
        with self.sems[ch].request() as req:
            for bs in packet.rss:
                for p in packet.overlapped_packets:
                    if packet.rss[bs] - p.rss[bs] < threshold:
                        packet.collided[bs] = True
                    if p.rss[bs] - packet.rss[bs] < threshold:
                        p.collided[bs] = True
                    p.overlapped_packets.remove(packet)
            self.packets_in_air[ch].remove(packet)
            packet.overlapped_packets= []
        gc.collect()
        if all(packet.collided.values()):
            return True
        return False


    # @staticmethod
    # def frequency_collision(p1: UplinkPacket, p2: UplinkPacket):
    #     """frequencyCollision, conditions
    #             |f1-f2| <= 120 kHz if f1 or f2 has bw 500
    #             |f1-f2| <= 60 kHz if f1 or f2 has bw 250
    #             |f1-f2| <= 30 kHz if f1 or f2 has bw 125
    #     """
    #
    #     p1_freq = p1.para.freq
    #     p2_freq = p2.para.freq
    #
    #     p1_bw = p1.para.bw
    #     p2_bw = p2.para.bw
    #
    #     if abs(p1_freq - p2_freq) <= 120000 and (p1_bw == 500 or p2_bw == 500):
    #         print("frequency coll 500")
    #         return True
    #     elif abs(p1_freq - p2_freq) <= 60000 and (p1_bw == 250 or p2_bw == 250):
    #         print("frequency coll 250")
    #         return True
    #     elif abs(p1_freq - p2_freq) <= 30000 and (p1_bw == 125 or p2_bw == 125):
    #         print("frequency coll 125")
    #         return True
    #
    #     print("no frequency coll")
    #     return False
