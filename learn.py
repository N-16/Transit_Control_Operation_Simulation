from simulation import SimulationEnv
from transit_info import *
from stop_info import *
from pax_info import *
from sim_info import *
import traceback
from datetime import datetime
import matplotlib.pyplot as plt

def plotLearning(x, scores, filename, lines=None, epsilons=None):
    fig =plt.figure()
    ax =fig.add_subplot(111, label="1")
    ax2 =fig.add_subplot(111, label="2", frame_on=False)

    if epsilons != None:
        ax.plot(x, epsilons, color="C0")
        ax.set_ylabel("Epsilon", color="C0")
    ax.set_xlabel("Game", color="C0")
    
    ax.tick_params(axis='x', colors="C0")
    ax.tick_params(axis='y', colors="C0")

    N = len(scores)
    running_avg = np.empty(N)
    
    for t in range(N):
	    running_avg[t] = np.mean(scores[max(0, t-20):(t+1)])

    ax2.scatter(x, running_avg, color="C1")
    #ax2.xaxis.tick_top()
    ax2.axes.get_xaxis().set_visible(False)
    ax2.yaxis.tick_right()
    #ax2.set_xlabel('x label 2', color="C1")
    ax2.set_ylabel('Score', color="C1")
    #ax2.xaxis.set_label_position('top')
    ax2.yaxis.set_label_position('right')
    #ax2.tick_params(axis='x', colors="C1")
    ax2.tick_params(axis='y', colors="C1")

    if lines is not None:
        for line in lines:
            plt.axvline(x=line)

    plt.savefig(filename)


try:
    with open('logs/log_' + str(datetime.now())+'.txt', 'a') as f:
        env = SimulationEnv(RL_TRANSIT_INFO, TRANSIT_SCHEDULE,
                             STOPS, PAX_DEMAND, START_TIME, END_TIME,
                               log_file=f, load_models=True)
        rewards = []
        epsilons = []
        cache_prev_epsilon = []
        first_itr = True
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
        x = [i+1 for i in range(len(rewards))]
        plotLearning(x, rewards, filename='plot_learn.png', epsilons=epsilons)
except:
    traceback.print_exc()