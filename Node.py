import numpy as np

from LoRaParameters import LoRaParameters
from Gateway import Gateway, DownlinkPacket
from TransmissionModel import AirInterface
from config import *

class NodeState(Enum):
    SLEEP = auto()
    TX = auto()
    RX = auto()

class Node():
    def __init__(self, nodeid, en_prof: EnergyProfile, lora_para:LoRaParameters, x, y,
        base_stations,  payload_size, air_interface:AirInterface, env ):
        self.id = nodeid
        self.para = lora_para
        self.x = x
        self.y = y
        print('node %d' %nodeid, "  @  (", self.x, ",", self.y,")")
        self.gain = 1
        self.energy_profile = energy_profile
        self.base_stations = base_stations
        self.process_time = process_time
        self.current_state = NodeState.SLEEP
        self.payload_size = payload_size
        self.air_interface = air_interface
        self.env = env

    def transmit( self, env_g):
        if (np.random.random()> env_g):
            self.current_state = NodeState.TX
            p = UplinkPacket(self, self.payload_size, np.random.randint(1,2000), self.air_interface)
            p.send(self.env.now)
            yield self.env.timeout(p.time_on_air)
            self.current_state = NodeState.RX
            yield self.env.timeout(config.DLtime)
            self.current_state = NodeState.SLEEP
        else:
            yield self.env.timeout(3000)

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
        return tx_power_mA[range(-2,21).index(tp_dbm)]*  self.Vdd * t

    def get_E_receive (self, bw, t):
        return rx_power_mA[[125,250,500].index(bw)] * self.Vdd * t


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
    def __init__(self, node: Node, payload_size,  id, interface):
        self.id = id
        self.node = node
        self.para = node.para
        self.payload_size = payload_size
        self.overlapped_packets = []
        self.received = False
        self.rss = {}
        self.snr = {}
        self.start_at = None
        self.end_at = None
        self.time_on_air = None
        self.transmissionInterface = interface

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
        self.end_at = self.start_at + self.airtime(self)
        self.transmissionInterface.register(self)
