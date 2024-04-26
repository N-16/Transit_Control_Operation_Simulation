from simulation import SimulationEnv
from transit_info import *
from stop_info import *
from pax_info import *
from sim_info import *
import traceback
from datetime import datetime
from util import plotLearning
from earlystop import EarlyStopper
from playsound import playsound



try:
    with open('../logs/log_' + str(datetime.now())+'.txt', 'a') as f:
        env = SimulationEnv(RL_5_TRANSIT_INFO, HET_TRANSIT_SCHEDULE,
                             STOPS, PAX_DEMAND, START_TIME, END_TIME,
                               log_file=f, load_models=False, save_models=True, save_data=False)
        rewards = []
        epsilons = []
        cache_prev_epsilon = []
        first_itr = True
        episodes = 100
        early_stopper = EarlyStopper()
        for i in range(1, episodes + 1):
            print("Episode ", i, "/", episodes)
            max_itr = 100000000000
            itr = 0
            if first_itr:
                first_itr = False
            else:
                env.reset()
            termination,_, __ = env.step(hourly_notice=True)
            r = 0
            while not termination and itr < max_itr:
                termination,reward, hour_complete = env.step(hourly_notice=True)
                itr += 1
                r += reward
                if hour_complete:
                    rewards.append(r)
                    r = 0
                    epsilons.append(env.transit[0].epsilon)
                    print("Average reward of last 50 =", sum(rewards[max(0, len(rewards) - 50):]) / len(rewards[max(0, len(rewards) - 50):]))
                    print('Epsilon:', env.transit[0].epsilon)
            #epsilons.append(env.transit[0].epsilon)
            #rewards.append(r)
            #print("Average reward of last 50 =", sum(rewards[max(0, len(rewards) - 50):]) / len(rewards[max(0, len(rewards) - 50):]))
            print("Average Waiting time= ", env.sim_data.get_avg_waiting())
            resp = input('Continue Train?(y/n)')
            if resp == 'n' or resp == 'N':
                break
            #print('Epsilon:', env.transit[0].epsilon)
            
            '''if early_stopper.earlyStop(rewards):
                playsound('extra/siren.wav')
                resp = input('Continue Train?(y/n)')
                if resp == 'n' or resp == 'N':
                    break
                else:
                    early_stopper.resetCounter()'''
        x = [i+1 for i in range(len(rewards))]
        plotLearning(x, rewards, filename='plot_learn.png', epsilons=epsilons)
except:
    traceback.print_exc()

