import numpy as np
from config import *

class FieldReconstructor:
    class LocalField:
        def __init__(self, id, init_temp):
            self.id = id
            self.s = init_temp
            self.t = 0 #time
            self.es_s_change = 0

            self.node_index_dict = {}
            self.w = []
            self.dw = np.array([])
            self.ds = {}
            self.hist = []

        def connect(self, other):
            self.node_index_dict[other] = len(self.w)
            other.node_index_dict[self] = len(other.w)
            self.w.append(0.1)
            other.w.append(0.1)
            self.hist.append(0)
            other.hist.append(0)

        def update(self, temp, time):
            self.ds[(temp - self.s)/(time - self.t)] = self.hist
            self.s = temp
            self.t = time
            self.es_s_change = 0
            self.hist = np.zeros(len(self.w))
            for d in self.node_index_dict:
                d.nearby_update(self)

            if len(self.ds) == 6:
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
            return self.s + (time - self.t) * np.dot(nearby_s- self.s, np.array(self.w))

    def __init__(self, node_ids, connection):
        self.nodes = {}
        for id in node_ids:
            self.nodes[id] = FieldReconstructor.LocalField(id, init_temp)
        for link in connection:
            self.nodes[link[0]].connect(self.nodes[link[1]])

    def update(self, node_id, temp, time):
        self.nodes[node_id].update(temp, time)







# X, Y = np.meshgrid(X_position, X_position)
# Z = np.zeros((estimator.T, X.shape[0], X.shape[1]))
# Tr = np.zeros((estimator.T, X.shape[0], X.shape[1]))
# # for i, device in enumerate(devices):
# #     print("Device %f @ (%.1f, %.1f)" %(device.id, device.state.location.x, device.state.location.y))
# #     print("(%.1f, %.1f)" %(X[i%N][i//N], Y[i%N][i//N]))
# chosen = random.sample(range(len(devices)), int(g))
#
# for t in range(estimator.T-1):
#     for i in chosen:
#         devices[i].update(t+1)
#     S = [a.get_temp(t+1) for a in devices]
#     Temp = [a._get_local_temp(t+1) for a in devices]
#     Z[t,:,:] = np.reshape(S, X.shape)
#     Tr[t, :, :] = np.reshape(Temp, X.shape)
#     chosen = random.sample(range(len(devices)), 60)
