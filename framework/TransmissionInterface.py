import numpy as np

from .LoRaParameters import LoRaParameters
from .Gateway import PacketRecord

class PropagationModel:
    # log distance path loss model (or log normal shadowing)
    def __init__(self, gamma=2.32, d0=1000.0, std=0.5, Lpld0=128.95, GL=0):
        self.gamma = gamma
        self.d0 = d0
        self.std = std
        if self.std < 0:
            self.std = 0
        self.Lpld0 = Lpld0
        self.GL = GL

    def tp_to_rss(self, indoor: bool, tp_dBm: int, d: float):
        bpl = 0  # building path loss
        if indoor:
            bpl = np.random.choice([17, 27, 21, 30])  # according Rep. ITU-R P.2346-0
        Lpl = 10 * self.gamma * np.log10(d / self.d0) + np.random.normal(self.Lpld0, self.std) + bpl
        if Lpl < 0:
            Lpl = 0
        return tp_dBm - self.GL - Lpl


class SNRModel:
    def __init__(self):
        self.noise = -2  # mean_mean_values
        self.std_noise = 1  # mean_std_values
        self.noise_floor = -174 + 10 * np.log10(125e3) + np.random.normal(self.noise, self.std_noise)

    def rss_to_snr(self, rss: float):
        return rss - self.noise_floor


class AirInterface:
    def __init__(self, sim_env, gateways, server, prop_model=None, snr_model=None):
        self.prop_model = prop_model
        self.snr_model = snr_model
        self.server = server
        self.sim_env = sim_env
        self.gateways = gateways
        if self.prop_model is None:
            self.prop_model = PropagationModel()
        if self.snr_model is None:
            self.snr_model = SNRModel()

    def transmit(self, p):
        dispatch = [self.sim_env.event() for i in range(len(self.gateways))]
        self.sim_env.process(self.server.receive_from_gateway(p, dispatch))

        for i in range(len(self.gateways)):
            gateway = self.gateways[i]
            dist = np.sqrt((p.node.x - gateway.x) ** 2 + (p.node.y - gateway.y) ** 2)
            rss = self.prop_model.tp_to_rss(False, p.para.tp, dist)
            snr = self.snr_model.rss_to_snr(rss)
            record = PacketRecord(p, gateway, rss, snr, dispatch[i])
            self.sim_env.process(gateway.listen(record))

