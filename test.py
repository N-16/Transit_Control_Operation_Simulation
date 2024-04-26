from simulation import SimulationEnv
from transit_info import *
from stop_info import *
from pax_info import *
from sim_info import *
import traceback
from datetime import datetime
import matplotlib.pyplot as plt
from util import plotLearning

try:
    with open('../logs/log_' + str(datetime.now())+'.txt', 'a') as f:
        env = SimulationEnv(RL_HET_4_TRANSIT_INFO, HET_TRANSIT_SCHEDULE,
                            STOPS, PAX_DEMAND, START_TIME, END_TIME,
                            log_file=f, load_models=True, 
                            save_models = False, control_op=True,
                            save_data=True)
        rewards = []
        first_itr = True
        episodes = 10
        avg_waiting = []
        for i in range(1, episodes + 1):
            print("Episode ", i, "/", episodes)
            max_itr = 1000000000
            itr = 0
            if first_itr:
                first_itr = False
            else:
                env.reset()
            termination,_,__ = env.step(learn=False)
            r = 0
            while not termination and itr < max_itr:
                termination,reward, _ = env.step(learn=False)
                itr += 1
                r += reward
            print("total reward =", r)
            rewards.append(r)
            avg_waiting.append(env.sim_data.get_avg_waiting())
        print("Average Reward: ", sum(rewards) / len(rewards))
        print("Averagge waiting in ", episodes, " episodes ", sum(avg_waiting) / len(avg_waiting))
        x = [i+1 for i in range(len(rewards))]
        plotLearning(x, rewards, filename='plot_test.png')
except:
    traceback.print_exc()