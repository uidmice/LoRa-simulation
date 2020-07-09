class Node():
    def __init__(self, nodeid, bs, period, datasize, x, y):
        self.nodeid = nodeid
        self.buffer = datasize
        self.bs = bs
        self.first = 1
        self.period = period
        self.lstretans = 0
        self.sent = 0
        self.coll = 0
        self.lost = 0
        self.noack = 0
        self.acklost = 0
        self.recv = 0
        self.losterror = 0
        self.rxtime = 0
        self.x = x
        self.y = y


        print('node %d' %nodeid, "x", self.x, "y", self.y)

        self.txpow = 0

        # graphics for node
        global graphics
        if (graphics == 1):
            global ax
            ax.add_artist(plt.Circle((self.x, self.y), 2, fill=True, color='blue'))

