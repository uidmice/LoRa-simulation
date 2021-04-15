import numpy as np
from config import *

class FieldReconstructor:
    class LocalField:
        def __init__(self, id, init_temp):
            self.id = id
            self.s = init_temp
            self.t = 0 #time

            self.node_index_dict = {}
            self.w = []
            self.dw = np.array([])
            self.ds = {}
            self.hist = []

        def connect(self, other):
            self.node_index_dict[other] = len(self.w)
            other.node_index_dict[self] = len(other.w)
            self.w.append(0.001)
            other.w.append(0.001)
            self.hist.append(0)
            other.hist.append(0)

        def update(self, temp, time):
            self.ds[time] = self.hist
            self.s = temp
            self.t = time
            self.hist = np.zeros(len(self.w))
            for d in self.node_index_dict:
                d.nearby_update(self)

            if len(self.ds) == 10:
                M = np.array([self.ds[a] for a in self.ds])
                w = np.linalg.pinv(M) @ np.array([[a for a in self.ds]]).T
                self.dw = w - np.array(self.w)
                self.w = w
                self.ds = {}
            return

        def nearby_update(self, update_node):
            assert update_node in self.node_index_dict
            idx = self.node_index_dict[update_node]
            self.hist[idx] += (update_node.s - self.s)/max(update_node.t - self.t, 1)

        def estimate(self, time):
            nearby_s = np.array([[a.s for a in self.node_index_dict]])
            return self.s + max(min((time - self.t) * np.dot(nearby_s- self.s, np.array(self.w))[0], 5), -5)

    def __init__(self, node_ids, connection):
        self.nodes = {}
        for id in node_ids:
            self.nodes[id] = FieldReconstructor.LocalField(id, init_temp)
        for link in connection:
            self.nodes[link[0]].connect(self.nodes[link[1]])

    def update(self, node_id, temp, time):
        self.nodes[node_id].update(temp, time)

    def field_estimate(self, node_id, time):
        assert node_id in self.nodes
        return self.nodes[node_id].estimate(time)

    def field_reconstruct(self, time):
        local = {}
        for node in self.nodes:
            local[node] = self.field_estimate(node, time)
        rt = {}
        for node in self.nodes:
            nearby = [n.id for n in self.nodes[node].node_index_dict]
            nearby.append(node)
            rt[node] = np.average([local[i] for i in nearby])
        return rt

