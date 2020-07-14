import numpy as np

from LoRaParameters import LoRaParameters
from TransmissionInterface import AirInterface
from config import *



class Gateway():
    SENSITIVITY = { 7:np.array([-123,-120,-116]),
                    8:np.array([-126,-123,-119]),
                    9:np.array([-129,-125,-122]),
                    10:np.array([-132,-128,-125]),
                    11:np.array([-133,-130.52,-128]),
                    12:np.array([-136,-133,-130])}
    SNR = { 7:-7.5, 8:-10, 9:-12.5,10:-15,11:-17.5,12:-20}
    NO_CHANNELS = 8

    def __init__(self, id, x, y, interface: AirInterface, env):
        self.id = id
        self.x = x
        self.y = y
        self.transmissionInterface = interface
        self.channels = range(NO_CHANNELS) #only listen to channel 0-7
        self.channel_states = np.zeros((NO_CHANNELS, )) #0 not busy, 1 busy
        self.env = env
        print('gateway %d' %id, "  @  (", self.x, ",", self.y,")")

    def listen(self):
        for p in self.transmissionInterface.packet_in_air:
            #######
            return




class DownlinkPacket:
    def __init__(self, not_received=False):
        self.not_received = not_received
