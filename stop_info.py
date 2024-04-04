import matplotlib.pyplot as plt
from enum import Enum

class AlightLevels(Enum):
    HIGH = 1
    MED = 2
    LOW = 3

STOPS = [{'index': 1}, {'index': 2},{'index': 3},
         {'index': 4}, {'index': 5},{'index': 6},
         {'index': 7}, {'index': 8},{'index': 9},
         {'index': 10}, {'index': 11},{'index': 12},
         {'index': 13}, {'index': 14},{'index': 15},
         {'index': 16}, {'index': 17},{'index': 18},]

# alight levels are not used
# arr rate in terms of passengers per minute
STOP_DEMAND = [{'index': 1, 'arr_rate': 2.3, 'alight_level': AlightLevels.HIGH}, #terminal
               {'index': 2, 'arr_rate': 1.0, 'alight_level': AlightLevels.LOW},
               {'index': 3, 'arr_rate': 0.8, 'alight_level': AlightLevels.LOW},
               {'index': 4, 'arr_rate': 1.2, 'alight_level': AlightLevels.LOW},
               {'index': 5, 'arr_rate':1.8, 'alight_level': AlightLevels.MED},
               {'index': 6, 'arr_rate':0.8, 'alight_level': AlightLevels.MED},
               {'index': 7, 'arr_rate':0.6, 'alight_level': AlightLevels.HIGH},
               {'index': 8, 'arr_rate':0.5, 'alight_level': AlightLevels.HIGH},
               {'index': 9, 'arr_rate':0.05, 'alight_level': AlightLevels.HIGH},
               {'index': 10, 'arr_rate':2.0, 'alight_level': AlightLevels.HIGH}, #terminal
               {'index': 11, 'arr_rate':0.8, 'alight_level': AlightLevels.LOW},
               {'index': 12, 'arr_rate':0.55, 'alight_level': AlightLevels.LOW},
               {'index': 13, 'arr_rate':0.9, 'alight_level': AlightLevels.LOW},
               {'index': 14, 'arr_rate':1.9, 'alight_level': AlightLevels.MED},
               {'index': 15, 'arr_rate':0.9, 'alight_level': AlightLevels.MED},
               {'index': 16, 'arr_rate':0.6, 'alight_level': AlightLevels.HIGH},
               {'index': 17, 'arr_rate':0.2, 'alight_level': AlightLevels.HIGH},
               {'index': 18, 'arr_rate':0.05, 'alight_level': AlightLevels.HIGH}]


x = []
y = []
for dmnd in STOP_DEMAND:
    x.append(dmnd['index'])
    y.append(dmnd['arr_rate'])

#plt.bar(x, y)
#plt.show()