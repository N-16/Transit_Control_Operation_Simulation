from simulation import SimulationEnv
from transit_info import *
from stop_info import *
from pax_info import *
from sim_info import *
import traceback
from datetime import datetime
from util import plotLearning
from earlystop import EarlyStopper



try:
    with open('../logs/log_' + str(datetime.now())+'.txt', 'a') as f:
        env = SimulationEnv(RL_4_TRANSIT_INFO, HET_TRANSIT_SCHEDULE,
                             STOPS, PAX_DEMAND, START_TIME, END_TIME,
                               log_file=f, load_models=False, save_models=True)
        rewards = []
        epsilons = []
        cache_prev_epsilon = []
        first_itr = True
        early_stopper = EarlyStopper()
        for i in range(1, 500):
            print("Episode ", i)
            max_itr = 10000
            itr = 0
            if first_itr:
                first_itr = False
            else:
                env.reset()
            termination,_ = env.step()
            r = 0
            while not termination and itr < max_itr:
                termination,reward = env.step()
                itr += 1
                r += reward
            print("total reward =", r)
            print('Epsilon:', env.transit[0].epsilon)
            epsilons.append(env.transit[0].epsilon)
            rewards.append(r)
            if early_stopper.earlyStop(r):
                resp = input('Continue Train?(y/n)')
                if resp == 'n' or resp == 'N':
                    break
            else:
                early_stopper.resetCounter()
        x = [i+1 for i in range(len(rewards))]
        plotLearning(x, rewards, filename='plot_learn.png', epsilons=epsilons)
except:
    traceback.print_exc()

def stopper():
