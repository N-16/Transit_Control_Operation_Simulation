from datetime import time, timedelta, datetime
from stop_info import STOP_DEMAND
import sim_info
import util
import random
import csv

import matplotlib.pyplot as plt
import numpy as np
#PAX_DEMAND = [{'id': 1, 'board_from': 2, 'alight_to': 3, 'arr_time': time(7,1,12)},
#              {'id': 2, 'board_from': 1, 'alight_to': 3, 'arr_time': time(7,2,0)}]



def generate_pax_demand(start_time, end_time, stop_demand, terminal_indices, peaks, arr_rate_variability=0.05):
    # for each stop
    pax_demand = []
    for stop in stop_demand:
        t = start_time
    #   while time < end time
        while t < end_time:
    #       time += time period based on arr rate and interval
            peak_inc = 0
            for peak in peaks:
                if(t > peak['from'] and t < peak['to']):
                    peak_inc = peak['inc']
                    break
                arr = ((stop['arr_rate'] * (1 + peak_inc)) + round(random.uniform(-arr_rate_variability,arr_rate_variability), 2))
                time_period = timedelta(minutes= 1 / max(0.02,arr))  
            
            t = util.add_time(t, time_period)
    #       add passenger
            if stop['index'] < max(terminal_indices):
                alight_to = random.randint(stop['index'] + 1, max(terminal_indices))
            else:
                alight_to = (random.randint(stop['index'], len(stop_demand)) % len(stop_demand)) + 1
            pax_demand.append({'id': len(pax_demand) + 1, 'board_from': stop['index'], 'alight_to': alight_to, 'arr_time': t})
    return pax_demand

PAX_DEMAND = generate_pax_demand(sim_info.PAX_START_TIME, sim_info.END_TIME, STOP_DEMAND, (1, 10), sim_info.PEAKS)

x = range(1, 19)
y_alight = np.zeros(18)
y_board = np.zeros(18)
for dmnd in PAX_DEMAND:
    y_alight[dmnd['alight_to'] - 1] = y_alight[dmnd['alight_to'] - 1] + 1
    y_board[dmnd['board_from'] - 1] = y_board[dmnd['board_from'] - 1] + 1

timestamp = str(datetime.now())
    
plt.bar(x=x, height=y_alight)
plt.xlabel('Stop')
plt.ylabel('Alighting Passengers')
plt.savefig('plots/stop_alight_trend_'+timestamp+'_.png')

plt.clf()

plt.bar(x=x, height=y_board)
plt.xlabel('Stop')
plt.ylabel('Boarding Passengers')
plt.savefig('plots/stop_board_trend_'+timestamp+'_.png')

keys = PAX_DEMAND[0].keys()

with open('pax_demand_csv/pax_demand_'+timestamp+'_.csv', 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(PAX_DEMAND)

    