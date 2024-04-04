import numpy as np
class EarlyStopper:
  def __init__(self, patience=40, min_delta=0.0001):
    self.patience = patience
    self.min_delta = min_delta
    self.counter = 0
    self.max_reward = -np.inf

  def earlyStop(self, reward_array):  
    avg_reward = np.mean(reward_array[max(0, len(reward_array)-10):(len(reward_array))])
    print("Avg reward of last 10:", avg_reward)
    if avg_reward > self.max_reward:
      self.max_reward = avg_reward
      self.counter = 0
    elif (avg_reward < (self.max_reward - self.min_delta)):
      self.counter += 1
      if self.counter >= self.patience:
        return True
    print(self.counter, " ", self.max_reward)
    return False
  
  def resetCounter(self):
    self.counter = 0