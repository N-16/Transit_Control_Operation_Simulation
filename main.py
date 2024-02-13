from simulation import SimulationEnv
from transit_info import *
from stop_info import *
from pax_info import *
import traceback

try:
    env = SimulationEnv(TRANSIT_INFO, TRANSIT_SCHEDULE, STOPS, PAX_DEMAND, time(6, 55, 0))
    max_itr = 10000
    itr = 0
    termination = env.step()
    while not termination and itr < max_itr:
        termination = env.step()
        itr += 1
except:
    traceback.print_exc()