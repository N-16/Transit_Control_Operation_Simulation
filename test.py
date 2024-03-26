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
        env = SimulationEnv(RL_4_TRANSIT_INFO, HET_TRANSIT_SCHEDULE,
                             STOPS, PAX_DEMAND, START_TIME, END_TIME,
                               log_file=f, load_models=True, save_models = False, control_op=True)
        rewards = []
        first_itr = True
        for i in range(1, 20):
            print("Episode ", i)
            max_itr = 10000
            itr = 0
            if first_itr:
                first_itr = False
            else:
                env.reset()
            termination,_ = env.step(learn=False)
            r = 0
            while not termination and itr < max_itr:
                termination,reward = env.step(learn=False)
                itr += 1
                r += reward
            print("total reward =", r)
            rewards.append(r)
        print("Average Reward: ", sum(rewards) / len(rewards))
        x = [i+1 for i in range(len(rewards))]
        plotLearning(x, rewards, filename='plot_test.png')
except:
    traceback.print_exc()