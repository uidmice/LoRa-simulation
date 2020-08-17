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

    def __init__(self, id, x, y, sim_env, adr_margin_db=10):
        self.id = id
        self.x = x
        self.y = y
        self.channels = range(Gateway.NO_CHANNELS) #only listen to channel 0-7
        # self.channel_states = np.zeros((NO_CHANNELS, )) #0 not busy, 1 busy
        self.sim_env = sim_env
        self.num_of_packet_received = 0

        if DEBUG:
            print('gateway %d' %id, "  @  (", self.x, ",", self.y,") on Chennels ", str(self.channels))

    def receive_packet(self, packet):
        sf = packet.para.sf
        bw = packet.para.bw
        snr_threshold = 5
        # print("RSS at gateway ", packet.rss[self.id])
        # print("channel: " , packet.para.channel)
        if (packet.para.channel in self.channels) and (packet.rss[self.id]>Gateway.SENSITIVITY[sf][[125, 250, 500].index(bw)]) :
            diff = packet.snr[self.id] - Gateway.SNR[sf]
                # print("diff: ", diff)
            if DEBUG:
                print("SNR difference at gateway ", self.id, ": ", diff)
            if diff > snr_threshold:
                packet.received[self.id] = True
                self.num_of_packet_received += 1
                return True

            if (diff > 0) and (np.random.random() < np.exp(1-snr_threshold/diff)): 
                packet.received[self.id] = True
                self.num_of_packet_received += 1
                return True
        return False

class DownlinkPacket:
    def __init__(self, adr_para = None, payload = None):
        self.adr_para = adr_para
        self.payload = payload
