# LoRa-simulation
LoRa network simulation

## Framework: 
- Node.py
  * Node: model of the end devices
  * EnergyProfile
  * UplinkPacket
- Gateway.py
  * Gateway: define sensitivity thresholds, receive packets
  * DownlinkPacket
- Server.py
  * Server: process packets received at gateways (mainly for ADR)
- LoRaParameters.py
  * LoRaParameters: available LoRa parameter settings
- TransmissionInterface.py
  * PropagationModel: tp to rss
  * SNRModel: rss to snr
  * AirInterface: check packet collision (of the same channel with the same SF)
- Enternal.py
  * RandomExternal: random environmental variable of space and time
  * ConstantExternal: constant environmental variable of space and time

## Simulation:
- LoRaNet.py [num_nodes] [sim_time(in minutes)]
- LoRaNet_test.py (for ALOHA)
- LoRaNet_test2.py (for ADR)
