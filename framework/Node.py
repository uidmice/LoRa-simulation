import math
import enum

from config import *
from .TransmissionInterface import AirInterface
from .LoRaParameters import LoRaParameters


class NodeStates(enum.Enum):
    SENDING_NO_COLLISION = 1
    SENDING_COLLISION = 2
    SLEEPING = 4


class Node:
    STATE_KEYWORDS = ["location", "failure_rate", "last_update", "current_sensing",
                      "num_unique_packets_received", "num_total_packets_sent", "total_transmit_time",
                      "total_receive_time", "total_energy_usage"]
    STATE_KEYS = []

    def __init__(self, node_id, energy_profile, lora_para: LoRaParameters,
                 air_interface: AirInterface, sim_env, location, adr,
                 adr_ack_limit=10, adr_ack_delay=5):
        self.id = node_id
        self.para = lora_para
        self.energy_profile = energy_profile
        self.payload_size = 10
        self._air_interface = air_interface
        self.sim_env = sim_env
        self.adr = adr
        self.packet_to_send = None

        self.location = location
        self.state = NodeStates.SLEEPING

        self._unique_packet_id = 0  # unique packets not counting for multiple tries
        self.unique_packet_received_successfully = []  # unique packets sent successfully received
        self.num_packets_sent = 0  # total number of packets sent

        self.transmit_time = {}
        self.receive_time = {}
        self.sensed_history = {}
        self.last_payload_sent = 0
        self.latest_sensed = 0
        self.last_payload_change = 0

        if DEBUG:
            print('node %d' % node_id, "  @  (", self.location.x, ",", self.location.y, ")", ", ch = ",
                  self.para.channel, ", sf = ",
                  self.para.sf, ", tp = ", self.para.tp)

        if adr:
            self.adr_ack_limit = adr_ack_limit
            self.adr_ack_delay = adr_ack_delay
            self.adr_ack_cnt = 0

    def __str__(self):
        return "Node {}".format(self.id)

    def get_status(self, *args, **kwargs):
        s = type('Status', (object,), {})()
        for arg in args:
            assert arg in Node.STATE_KEYWORDS, "%s not a valid keyword"
            if arg == "location":
                s.location = self.location
            elif arg == "failure_rate":
                s.failure_rate = self.failure_rate()
            elif arg == "last_update":
                s.last_update = self.last_payload_sent
            elif arg == "current_sensing":
                s.current_sensing = self.latest_sensed
            elif arg == "num_unique_packets_received":
                s.num_unique_packets_received = len(self.unique_packet_received_successfully)
            elif arg == "num_total_packets_sent":
                s.num_total_packets_sent = self.num_packets_sent
            elif arg == "total_transmit_time":
                s.total_transmit_time = sum(self.transmit_time.values())
            elif arg == "total_receive_time":
                s.total_receive_time = sum(self.receive_time.values())
            elif arg == "total_energy_usage":
                s.total_energy_usage = self.energy_profile.usage
            else:
                assert False, "%s is not defined"

        for key, value in kwargs:
            assert key in Node.STATE_KEYS

        return s

    def create_unique_packet(self, payload, adr=True, adrAckReq=False):
        packet = UplinkPacket(self, self._unique_packet_id, payload, adr, adrAckReq)
        self._unique_packet_id += 1
        return packet

    def send(self, packet):
        self.packet_to_send = packet
        self.num_packets_sent += 1
        self.state = NodeStates.SENDING_NO_COLLISION
        yield self.sim_env.process(packet.schedule())

        # not accounting energy cost to run on-device algorithm
        self.energy_profile.usage += self.energy_profile.transmit_energy_cost(packet.para.tp, packet.time_on_air)
        self.transmit_time[self.sim_env.now] = packet.time_on_air
        yield packet.receive

        if packet.received:
            self.unique_packet_received_successfully.append(packet.id)
            self.last_payload_change = self.latest_sensed - self.last_payload_sent
            self.last_payload_sent = self.latest_sensed
        else:
            self.last_payload_change = 0
        if self.adr:
            self.ed_adr()
        self.state = NodeStates.SLEEPING

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

    def failure_rate(self):
        if self._unique_packet_id == 0:
            return 0
        return 1 - len(self.unique_packet_received_successfully)/ float(self.num_packets_sent)


    def sense(self, environment):
        value = environment.sense(self.location)
        self.sensed_history[self.sim_env.now] = value
        self.latest_sensed = value
        return value

    @property
    def air_interface(self):
        return self._air_interface


class EnergyProfile:
    rx_power_mA = [10.3, 11.1, 12.6]

    # Transmit consumption in mA from -2 to +17 dBm
    tx_power_mA = [22, 22, 22, 23,  # RFO/PA0: -2..1
                   24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
                   82, 85, 90,  # PA_BOOST/PA1: 15..17
                   105, 115, 125, 135]  # PA_BOOST/PA1+PA2: 18..20

    def __init__(self, proc_power=0.1, Vdd=3.3, E_tot=BATTERY_ENERGY):
        self.proc_power_mW = proc_power
        self.Vdd = Vdd
        self.origin_E_tot = E_tot
        self.usage = 0

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
    def __init__(self, node: Node, id, payload=0, adr=True, adrAckReq=False):
        self.id = node.id
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

        self.transmission = None
        self.dl = None
        self.receive = None

    def airtime(self):  # in ms
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
        if t > 0:
            yield self.node.sim_env.timeout(t)
        self.transmission = self.node.sim_env.process(self.send())
        yield self.transmission

    def send(self):
        if DEBUG:
            print(str(self.node.sim_env.now) + ": " + str(self) + " is being sent\t TOA: " + str(self.time_on_air) + " ms")
        self.node.air_interface.transmit(self)
        self.receive = self.node.sim_env.event()
        yield self.node.sim_env.timeout(self.time_on_air)

    def __str__(self):
        return "Packet #{} from Node {}".format(self.id, self.node.id)
