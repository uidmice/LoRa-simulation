class LoRaParameters:

    SPREADING_FACTORS = [12, 11, 10, 9, 8, 7]
    BAND_WIDTH = [125, 250, 500]
    CHANNELS = range(902300000, 915000000, 200000)
    TP_DBM = range(0, 22)

    def __init__(self, channel, sf=12, tp=15, cr=1,bw = 125):
        assert (bw == 125), "Only 125kHz bandwidth is supported"
        assert (sf  in LoRaParameters.SPREADING_FACTORS), "SF needs to be between [7, 12]"
        assert (channel in range(len(LoRaParameters.CHANNELS))), "Channel needs to be between [0, 63]"
        assert (tp in LoRaParameters.TP_DBM), "TP needs to be  between [0, 20]"
        self.freq = LoRaParameters.CHANNELS[channel]
        self.channel = channel
        self.sf = sf
        self.bw = bw
        self.cr = cr
        self.tp = tp
        self.h = 0

        if bw == 125 and sf in [11, 12]:
            # low data rate optimization mandated for BW125 with SF11 and SF12
            self.de = 1
        else:
            self.de = 0
        if sf == 6:
            self.h = 1


    def change_sf_to(self, sf: int):
        assert (12 >= sf >= 7), "SF needs to be between [7, 12]"
        if self.bw == 125 and self.sf in [11, 12]:
            # low data rate optimization mandated for BW125 with SF11 and SF12
            self.de = 1
        else:
            self.de = 0
        if self.sf == 6:
            # can only have implicit header with SF6
            self.h = 1
        else:
            self.h = 0

    def change_tp_to(self, tp: int):
        tmp = tp
        if tmp > 14 or tmp < 2:
            raise ValueError('Out of bound TP changing from ' + str(self.tp) + ' to ' + str(tmp))
        self.tp = tmp
    def change_freq_to(self, freq):
        assert (freq in LoRaParameters.CHANNELS), "frequency not valid"
        self.freq = freq
        self.channel = LoRaParameters.CHANNELS.index(freq)

    def change_channel_to(self, channel):
        assert (channel in range(64)), "Channel needs to be between [0, 63]"
        self.freq = LoRaParameters.CHANNELS[channel]
        self.channel = channel

    def __str__(self):
        return 'SF{}BW{}TP{}'.format(int(self.sf), int(self.bw), int(self.tp))
