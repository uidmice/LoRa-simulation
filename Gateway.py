import numpy as np

from LoRaParameters import LoRaParameters
from config import *

class Gateway:
    SENSITIVITY = { 7:np.array([-123,-120,-116]),
                    8:np.array([-126,-123,-119]),
                    9:np.array([-129,-125,-122]),
                    10:np.array([-132,-128,-125]),
                    11:np.array([-133,-130.52,-128]),
                    12:np.array([-136,-133,-130])}
    SNR = { 7:-7.5, 8:-10, 9:-12.5,10:-15,11:-17.5,12:-20}
    NO_CHANNELS = 8

    def __init__(self, id, x, y, sim_env):
        self.id = id
        self.x = x
        self.y = y
        self.channels = range(Gateway.NO_CHANNELS) #only listen to channel 0-7
        # self.channel_states = np.zeros((NO_CHANNELS, )) #0 not busy, 1 busy
        self.sim_env = sim_env
        print('gateway %d' %id, "  @  (", self.x, ",", self.y,")")

    def receive_packet(self, packet):
        sf = packet.para.sf
        bw = packet.para.bw
        snr_threshold = 10.0
        if packet.para.channel in self.channels:
            if packet.rss[self.id]>Gateway.SENSITIVITY[sf][[125, 250, 500].index(bw)]:
                diff = packet.snr[self.id] - Gateway.SNR[sf]
                if diff > snr_threshold:
                    packet.received[self.id] = True
                elif diff > 0:
                    if np.random.random() < np.exp(1-snr_threshold/diff):
                        packet.received[self.id] = True
        return packet.received[self.id]

class DownlinkPacket:
    def __init__(self, not_received=False):
        self.not_received = not_received
