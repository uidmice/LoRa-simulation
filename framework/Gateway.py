import numpy as np

from config import *
from .utils import PacketStatus, PacketRecord

class Gateway:
    SENSITIVITY = { 7:np.array([-123,-120,-116]),
                    8:np.array([-126,-123,-119]),
                    9:np.array([-129,-125,-122]),
                    10:np.array([-132,-128,-125]),
                    11:np.array([-133,-130.52,-128]),
                    12:np.array([-136,-133,-130])}
    SNR = { 7:-7.5, 8:-10, 9:-12.5,10:-15,11:-17.5,12:-20}
    SNR_THRESHOLD = 5
    NO_CHANNELS = 8

    def __init__(self, id, location, sim_env):
        self.id = id
        self.location = location
        self.channels = range(Gateway.NO_CHANNELS) #only listen to channel 0-7
        self.sim_env = sim_env
        self.num_of_packet_received = 0
        self.receiving = []
        self.record = []

        if DEBUG:
            print('gateway %d' %id, "  @  (", self.location.x, ",", self.location.y,") on Channels ", str(self.channels))

    def listen(self, re: PacketRecord):
        if re.parameter.channel not in self.channels:
            re.status = PacketStatus.NOT_LISTEN   # Not listening to the channel
            re.dispatch.succeed(value={self.id: re})
        else:
            if re.rss < Gateway.SENSITIVITY[re.parameter.sf][[125, 250, 500].index(re.parameter.bw)]:
                re.status = PacketStatus.WEAK_RSS  # RSS to low, weak packet
                re.dispatch.succeed(value={self.id: re})
            else:
                diff = re.snr - Gateway.SNR[re.parameter.sf]
                if ( diff <= 0) or (diff < Gateway.SNR_THRESHOLD and np.random.random() > np.exp(1-Gateway.SNR_THRESHOLD/diff)):
                    re.status = PacketStatus.WEAK_SNR # SNR to low, weak packet
                    re.dispatch.succeed(value={self.id: re})
                else:
                    for packet in self.receiving:
                        if packet.parameter.sf == re.parameter.sf and packet.parameter.channel == re.parameter.channel and re.rss - packet.rss < 10:
                            re.status = PacketStatus.COLLIDED
                            re.dispatch.succeed(value={self.id: re})
                            break
                    for packet in self.receiving:
                        if packet.status == PacketStatus.OK:
                            if packet.parameter.sf == re.parameter.sf and  packet.parameter.channel == re.parameter.channel and packet.rss - re.rss  < 10:
                                packet.status = PacketStatus.COLLIDED
                                packet.dispatch.succeed(value={self.id: packet})
        self.record.append(re)
        self.receiving.append(re)
        yield re.transmission
        self.receiving.remove(re)

        if not re.dispatch.triggered:
            re.dispatch.succeed(value={self.id: re})
        return

    def reset(self, sim_env):
        self.sim_env = sim_env
        self.num_of_packet_received = 0
        self.receiving = []
        self.record = []

class DownlinkPacket:
    def __init__(self, adr_para = None, payload = None):
        self.adr_para = adr_para
        self.payload = payload
