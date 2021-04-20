import numpy as np
from config import *
import random

class FieldReconstructor:
    class LocalField:
        def __init__(self, id, init_temp):
            self.id = id
            self.s = init_temp
            self.t = 0 #time
            self.changes = 0
            self.dchanges = 0

            self.node_index_dict = {}
            self.w = None
            self.ds = {}
            self.hist = None
            self.num_nearby = 0

        def connect(self, other):
            self.node_index_dict[other] = self.num_nearby
            other.node_index_dict[self] = other.num_nearby
            self.num_nearby += 1
            other.num_nearby += 1
            self.w = np.ones(self.num_nearby) *0.005
            other.w = np.ones(other.num_nearby) *0.005
            self.hist = np.zeros(self.num_nearby)
            other.hist = np.zeros(other.num_nearby)

        def update(self, temp, time):
            changes = (temp - self.s) / max(time - self.t, 1)
            self.dchanges = (changes - self.changes)/ max(time - self.t, 1)
            self.changes = changes
            # self.ds[time - self.t] = self.hist
            # self.s = temp
            # self.t = time
            # self.hist = np.zeros(self.num_nearby)
            #
            # for d in self.node_index_dict:
            #     d.nearby_update(self)
            #
            # if len(self.ds) == 6:
            #     M = np.array([self.ds[a] for a in self.ds])
            #     w = np.linalg.pinv(M) @ np.array([[a for a in self.ds]]).T
            #
            #     self.dw = w - self.w
            #     self.w = w
            #     self.ds = {}
            # return

        def nearby_update(self, update_node):
            assert update_node in self.node_index_dict
            idx = self.node_index_dict[update_node]
            self.hist[idx] += (update_node.s - self.s)/max(update_node.t - self.t, 1)

        def estimate(self, time):
            return self.s + self.changes * (time - self.t), self.t, time - self.t
            # nearby_s = np.array([[a.s for a in self.node_index_dict]])
            # changes = (time - self.t) * np.dot(nearby_s- self.s, self.w)[0]
            # return self.s + min(max(changes, 5), -5), changes

    def __init__(self, node_ids, connection, field_update):
        self.nodes = {}
        self.field_update = field_update
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
        last_time = {}
        empty_time = {}
        for node in self.nodes:
            local[node], last_time[node], empty_time[node] = self.field_estimate(node, time)
        list = [k for k, v in sorted(empty_time.items(), key=lambda item: item[1])]
        for node in list:
            nearby = [n.id for n in self.nodes[node].node_index_dict]
            if last_time[node] == 0:
                local[node] = np.average([local[i] for i in nearby])
            elif empty_time[node] > 4* self.field_update:
                local[node] = 0.2 * local[node] + 0.8 * np.average([local[i] for i in nearby])
        return local

