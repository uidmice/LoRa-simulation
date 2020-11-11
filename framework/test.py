from framework.Node import *
from framework.Gateway import Gateway
from framework.TransmissionInterface import AirInterface
from framework.Server import Server, Application
from framework.LoRaParameters import LoRaParameters
from framework.External import TempExternal
from config import *
nodes = []
gateways = []

sim_env = simpy.Environment()
external = TempExternal(sim_env)
gateways.append(Gateway(0, 500, 0,  sim_env))
gateways.append(Gateway(1, -500, 0,  sim_env))
server = Server(gateways, sim_env, Application())
air_interface = AirInterface(sim_env, gateways, server)

def node_send(node: Node, t):
    for i in range(50):
        yield sim_env.timeout(np.random.randint(t/2))
        packet = UplinkPacket(node, np.random.randint(50), adr=True, adrAckReq=True)
        yield sim_env.process(node.send(packet))
        yield sim_env.timeout(t * (i+1)-sim_env.now)


n_id = 0
for i in range(-CORD+5,CORD+1,10):
    for j in range(-CORD+5,CORD+1,10):
        x = j * GRID
        y = i * GRID
        node = Node(n_id, EnergyProfile(3.3), LoRaParameters(i%Gateway.NO_CHANNELS, sf = 12), x,
              y, air_interface, sim_env, NodeStatus(n_id), True)
        nodes.append(node)
        sim_env.process(node_send(node, 6000))
        n_id += 1



sim_env.run()