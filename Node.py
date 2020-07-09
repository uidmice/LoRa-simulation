import numpy as np

import config


class myNode():
    def __init__(self, nodeid, period, x, y):
        self.nodeid = nodeid
        self.period = period
        self.x = x
        self.y = y
        self.gain = 0.39
        self.sent = 0
        self.coll = 0
        self.recv = 0
        self.losterror = 0
        self.rxtime = 0
        print('node %d' %nodeid, "  @  (", self.x, ",", self.y,")")

class EnergyProfile:
    rx_power_mA = [10.3, 11.1, 12.6]

    # Transmit consumption in mA from -2 to +17 dBm
    tx_power_mA = [22, 22, 22, 23,                                      # RFO/PA0: -2..1
          24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
          82, 85, 90,                                          # PA_BOOST/PA1: 15..17
          105, 115, 125]                                       # PA_BOOST/PA1+PA2: 18..20
    tx_power_cof_k = 0.6
    tx_power_cof_b = 17
    def __init__(self, proc_power, Vdd = 3.3):
        self.proc_power_mW = proc_power
        self.Vdd = Vdd

    def get_E_compute(t):
        return self.proc_power_mW * t

    def get_E_transmit(tp_dbm, t):
        # return (10**(tp_dbm/10.0) * tx_power_cof_k + tx_power_cof_b) *  self.Vdd * t
        return tx_power_mA[range(-2,21).index(tp_dbm)]*  self.Vdd * t

    def get_E_receive (bw, t):
        return rx_power_mA[[125,250,500].index(bw)] * self.Vdd * t


class BaseStation():
    def __init__(self, id, x, y):
        self.bsid = id
        self.x = x
        self.y = y
        print('gateway %d' %id, "  @  (", self.x, ",", self.y,")")
        self.nrCollisions = 0
        self.nrReceived = 0
        self.nrProcessed = 0
        self.nrLost = 0
        self.nrLostError = 0
        self.nrNoACK = 0
        self.nrACKLost = 0


class Packet():
    def __init__(self, nodeid, bsid, freq, sf, bw, cr, tp_dbm):
        self.nodeid = nodeid
        self.freq = freq
        self.sf = sf
        self.bw = bw
        self.cr = cr
        self.tp_dbm = tp_dbm
        self.pl = config.LorawanHeader+config.PcktLength_SF[self.sf-7]
        self.symTime = (2.0**self.sf)/self.bw
        self.tof = airtime(self.sf,self.cr,self.pl,self.bw)
        print( "ToF (Time of Flight) node ", self.nodeid, "  ", self.tof)
        # denote if packet is collided
        self.collided = 0
        self.processed = 0
        self.lost = False
        self.perror = False
        self.acked = 0
        self.acklost = 0

    def airtime(sf,cr,pl,bw): #in ms
        H = 0        # implicit header disabled (H=0) or not (H=1)
        DE = 0       # low data rate optimization enabled (=1) or not (=0)
        Npream = 8   # number of preamble symbol (12.25  from Utz paper)

        if bw == 125 and sf in [11, 12]:
            # low data rate optimization mandated for BW125 with SF11 and SF12
            DE = 1
        if sf == 6:
            # can only have implicit header with SF6
            H = 1

        Tsym = (2.0**sf)/bw  # msec
        Tpream = (Npream + 4.25)*Tsym
        print ("sf:", sf, " cr:", cr, " pl:", pl, " bw:", bw)
        payloadSymbNB = 8 + max(math.ceil((8.0*pl-4.0*sf+28+16-20*H)/(4.0*(sf-2*DE)))*(cr+4),0)
        Tpayload = payloadSymbNB * Tsym
        return Tpream + Tpayload


# def transmit(env,node):
#     while node.buffer > 0.0:
#         node.packet.rssi = node.packet.txpow - Lpld0 - 10*gamma*math.log10(node.dist/d0) - np.random.normal(-var, var)
#         # add maximum number of retransmissions
#         if (node.lstretans and node.lstretans <= 8):
#             node.first = 0
#             node.buffer += PcktLength_SF[node.parameters.sf-7]
#             # the randomization part (2 secs) to resove the collisions among retrasmissions
#             yield env.timeout(max(2+airtime(12, CodingRate, AckMessLen+LorawanHeader, Bandwidth), float(node.packet.rectime*((1-0.01)/0.01)))+(random.expovariate(1.0/float(2000))/1000.0))
#         else:
#             node.first = 0
#             node.lstretans = 0
#             yield env.timeout(random.expovariate(1.0/float(node.period)))
#
#         node.buffer -= PcktLength_SF[node.parameters.sf-7]
#         print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#
#         # time sending and receiving
#         # packet arrives -> add to base station
#         node.sent = node.sent + 1
#         if (node in packetsAtBS):
#             print "ERROR: packet already in"
#         else:
#             sensitivity = sensi[node.packet.sf - 7, [125,250,500].index(node.packet.bw) + 1]
#             if node.packet.rssi < sensitivity:
#                 print "node {}: packet will be lost".format(node.nodeid)
#                 node.packet.lost = True
#             else:
#                 node.packet.lost = False
#                 if (per(node.packet.sf,node.packet.bw,node.packet.cr,node.packet.rssi,node.packet.pl) < random.uniform(0,1)):
#                     # OK CRC
#                     node.packet.perror = False
#                 else:
#                     # Bad CRC
#                     node.packet.perror = True
#                 # adding packet if no collision
#                 if (checkcollision(node.packet)==1):
#                     node.packet.collided = 1
#                 else:
#                     node.packet.collided = 0
#
#                 packetsAtBS.append(node)
#                 node.packet.addTime = env.now
#
#         yield env.timeout(node.packet.rectime)
#
#         if (node.packet.lost == 0\
#                 and node.packet.perror == False\
#                 and node.packet.collided == False\
#                 and checkACK(node.packet)):
#             node.packet.acked = 1
#             # the packet can be acked
#             # check if the ack is lost or not
#             if((14 - Lpld0 - 10*gamma*math.log10(node.dist/d0) - np.random.normal(-var, var)) > sensi[node.packet.sf-7, [125,250,500].index(node.packet.bw) + 1]):
#             # the ack is not lost
#                 node.packet.acklost = 0
#             else:
#             # ack is lost
#                 node.packet.acklost = 1
#         else:
#             node.packet.acked = 0
#
#         if node.packet.processed == 1:
#             global nrProcessed
#             nrProcessed = nrProcessed + 1
#         if node.packet.lost:
#             #node.buffer += PcktLength_SF[node.parameters.sf-7]
#             print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#             node.lost = node.lost + 1
#             node.lstretans += 1
#             global nrLost
#             nrLost += 1
#         elif node.packet.perror:
#             print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#             node.losterror = node.losterror + 1
#             global nrLostError
#             nrLostError += 1
#         elif node.packet.collided == 1:
#             #node.buffer += PcktLength_SF[node.parameters.sf-7]
#             print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#             node.coll = node.coll + 1
#             node.lstretans += 1
#             global nrCollisions
#             nrCollisions = nrCollisions +1
#         elif node.packet.acked == 0:
#             #node.buffer += PcktLength_SF[node.parameters.sf-7]
#             print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#             node.noack = node.noack + 1
#             node.lstretans += 1
#             global nrNoACK
#             nrNoACK += 1
#         elif node.packet.acklost == 1:
#             #node.buffer += PcktLength_SF[node.parameters.sf-7]
#             print "node {0.nodeid} buffer {0.buffer} bytes".format(node)
#             node.acklost = node.acklost + 1
#             node.lstretans += 1
#             global nrACKLost
#             nrACKLost += 1
#         else:
#             node.recv = node.recv + 1
#             node.lstretans = 0
#             global nrReceived
#             nrReceived = nrReceived + 1
#
#         # complete packet has been received by base station
#         # can remove it
#         if (node in packetsAtBS):
#             packetsAtBS.remove(node)
#             # reset the packet
#         node.packet.collided = 0
#         node.packet.processed = 0
#         node.packet.lost = False
#         node.packet.acked = 0
#         node.packet.acklost = 0
