
# IS7 = np.array([1,-8,-9,-9,-9,-9])
# IS8 = np.array([-11,1,-11,-12,-13,-13])
# IS9 = np.array([-15,-13,1,-13,-14,-15])
# IS10 = np.array([-19,-18,-17,1,-17,-18])
# IS11 = np.array([-22,-22,-21,-20,1,-20])
# IS12 = np.array([-25,-25,-25,-24,-23,1])
# IsoThresholds = np.array([IS7,IS8,IS9,IS10,IS11,IS12])

Bandwidth = 125
CodingRate = 1


graphics = 1

DLtime = 1000 # msec
MAX_RETRY = 20

MAX_DISTANCE = 5000 # 5 km
GRID = 100 #100m
CORD = int(MAX_DISTANCE/GRID)

MINUTE_TO_MS = 60000 # minute to ms
UPDATA_RATE = 60000 #update external environment every 1 minute
