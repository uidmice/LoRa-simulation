import numpy as np
from config import *
from collections import deque

from .Gateway import DownlinkPacket, PacketStatus, Gateway
from .LoRaParameters import LoRaParameters
from .Node import NodeStates
from .utils import PacketInformation
from .FieldReconstruction import FieldReconstructor

class Application:
    def __init__(self, node_ids, connection, field_update):
        self.fusion_center = FieldReconstructor(node_ids, connection, field_update)

    def run(self, info):
        temp = info.payload['value']
        time = info.payload['time']
        self.fusion_center.update(info.node_id, temp, time)


    def reset(self):
        self.data = {}


class Server:
    def __init__(self, gateways, sim_env, application, num_measurements = 5, adr_margin_db = 10, mode = 3):
        self.gateways = gateways
        self.sim_env = sim_env
        self.history = []
        self.application = application
        #ADR:   mode = 1: average, 2: max, 3: min
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

    def receive_from_gateway(self, p, dispatch):
        ret = yield self.sim_env.all_of(dispatch)
        ret = {k: v for d in ret.values() for k, v in d.items()}
        info = PacketInformation(p.id, p.node.id, p.payload, p.payload_size)
        for gateway_id, packet_record in ret.items():
            info.snr[gateway_id] = packet_record.snr
            info.status[gateway_id] = packet_record.status

        self.history.append(info)
        if p.node.id not in self.packet_num_received_from:
            self.packet_num_received_from[p.node.id] = 0
            self.packet_snr_history[p.node.id] =deque(maxlen=self.num_measurements)
            self.adr_for_node[p.node.id] = None

        dl = None
        if any([a==PacketStatus.OK for a in info.status.values()]):
            self.packet_num_received_from[p.node.id] += 1
            dl = DownlinkPacket()
            p.received = True
            if info.payload:
                self.application.run(info)
            if not p.adr:
                self.packet_snr_history[p.node.id].clear()
                self.adr_for_node[p.node.id] = None

        else:
            p.lost_cnt += 1
        if any([a==PacketStatus.COLLIDED for a in info.status.values()]):
            p.node.state = NodeStates.SENDING_COLLISION
        if p.adr:
            dl = self.adr_process(info, p, dl)
        yield self.sim_env.timeout(np.random.randint(2000))  # randomly wait for 0~2s for the downlink
        p.dl = dl
        p.receive.succeed()

    def adr_process(self, packet_info: PacketInformation,packet, dl):
        best_snr = max(packet_info.snr.values())
        self.packet_snr_history[packet_info.node_id].append(best_snr)
        if DEBUG:
            print("SNR measurement collected: ", best_snr)
            print(self.packet_snr_history[packet.node.id])

        if dl:
            if len(self.packet_snr_history[packet_info.node_id]) == self.num_measurements:
                SNR_M = self.f(self.packet_snr_history[packet_info.node_id])
                sf = packet.para.sf
                tp = packet.para.tp
                SNR_Req = Gateway.SNR[sf]
                margin = SNR_M - SNR_Req - self.adr_margin_db
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
                self.packet_snr_history[packet_info.node_id].clear()
                if not (sf == packet.para.sf and tp == packet.para.tp):
                    dl.adr_para = self.adr_for_node[packet.node.id]
            if packet.adrAckReq:
                dl.adr_para = self.adr_for_node[packet.node.id]
        return dl

    def reset(self, sim_env):
        self.sim_env = sim_env
        self.history = []
        self.application.reset()
        self.packet_snr_history = dict()  # node id : [snr]
        self.packet_num_received_from = dict()  # node id : num_packets
        self.adr_for_node = dict()