from Gateway import DownlinkPacket, Gateway
from LoRaParameters import LoRaParameters
import numpy as np
from config import *
from collections import deque

class Server:
    def __init__(self, num_measurements = 5, adr_margin_db = 10, mode = 1):
        #mode = 1: average, 2: max, 3: min
        self.packet_snr_history = dict() # node id : [snr]
        self.packet_num_received_from = dict() # node id : num_packets
        self.adr_for_node = dict()
        self.num_measurements = num_measurements
        self.adr_margin_db = adr_margin_db  # dB
        if mode == 1:
            self.f = lambda hist: np.mean(hist)
        elif mode == 2:
            self.f = lambda hist: np.max(hist)
        else:
            self.f = lambda hist: np.min(hist)

    def process(self, packet):
        if packet.node.id not in self.packet_num_received_from:
            self.packet_num_received_from[packet.node.id] = 0
            self.packet_snr_history[packet.node.id] =deque(maxlen=self.num_measurements)
            self.adr_for_node[packet.node.id] = None
        lost = not any(packet.received.values())
        if lost:
            best_snr = max(packet.snr.values())
            self.packet_snr_history[packet.node.id].append(best_snr)
            if DEBUG:
                print(str(packet), " too weak.")
                print("SNR measurement collected: ", best_snr)
                print(self.packet_snr_history[packet.node.id])
            return None

        self.packet_num_received_from[packet.node.id] += 1
        dl = DownlinkPacket()

        if not packet.adr:
            self.packet_snr_history[packet.node.id].clear()
            self.adr_for_node[packet.node.id] = None

        else:
            best_snr = max(packet.snr.values())
            self.packet_snr_history[packet.node.id].append(best_snr)
            if DEBUG:
                print("SNR measurement collected: ", best_snr)
                print(self.packet_snr_history[packet.node.id])
            if len(self.packet_snr_history[packet.node.id]) == self.num_measurements:
                SNR_Max = self.f(self.packet_snr_history[packet.node.id])
                sf = packet.para.sf
                tp = packet.para.tp
                SNR_Req = Gateway.SNR[sf]
                margin = SNR_Max - SNR_Req - self.adr_margin_db
                Nstep = np.round(margin/3)
                while Nstep>0 and sf > min(LoRaParameters.SPREADING_FACTORS):
                    sf -= 1
                    Nstep -= 1
                while Nstep > 0 and tp > min(LoRaParameters.TP_DBM):
                    tp -= 3
                    Nstep -= 1
                while Nstep < 0 and tp < max(LoRaParameters.TP_DBM):
                    tp += 3
                    Nstep += 1
                self.adr_for_node[packet.node.id] = {'sf': sf, 'tp': tp}
                if not (sf == packet.para.sf and tp == packet.para.tp):
                    dl.adr_para = self.adr_for_node[packet.node.id]
        if packet.adrAckReq:
            dl.adr_para = self.adr_for_node[packet.node.id]
        packet.dl = dl
        return dl
