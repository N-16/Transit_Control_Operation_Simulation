from enum import Enum
from datetime import time
import random
import dueling_dqn
import numpy as np
import torch as T
class TransitState(Enum):
    TO_DISPATCH = 1
    STOP = 2
    MOVING = 3
    SERVED = 5

class EventType(Enum):
    INIT = 1
    DISPATCH = 2
    STOP = 3
    DEPART = 4

class PaxState(Enum):
    TO_BOARD = 1
    ON_BOARD = 2
    ARRIVED = 3
    
class Transit:
    def __init__(self, id: int, capacity: int, controllable = False):
        self.capacity = capacity
        self.state = TransitState.TO_DISPATCH 
        self.id = id
        self.last_stop_index = 0
        self.occupancy = 0
        self.controllable = controllable
    def get_action(self):
        if random.uniform(0, 1) > 0.75:
            return True
        return False
    
class RLTransit(Transit):
    def __init__(self, id: int, capacity: int, gamma:float, epsilon:float, alpha:float,
                n_actions:int, input_dims:tuple, mem_size:int, batch_size:int,
                eps_min:float, eps_decay:float, replace = 1000, chkpt_dir = 'models'
                ,controllable=False):
        super().__init__(id, capacity, controllable)
        self.gamma = gamma
        self.epsilon = epsilon
        self.eps_min = eps_min
        self.eps_dec = eps_decay
        self.action_space = [i for i in range(n_actions)]
        self.learn_step_counter = 0
        self.batch_size = batch_size
        self.replace_target_cnt = replace
        self.memory = dueling_dqn.ReplayBuffer(mem_size, input_dims, n_actions)

        self.q_eval = dueling_dqn.DuelingLinearDeepQNetwork(alpha, n_actions,
                                    input_dims=input_dims,
                                   name='q_eval', chkpt_dir=chkpt_dir)
        self.q_next = dueling_dqn.DuelingLinearDeepQNetwork(alpha, n_actions,
                                    input_dims=input_dims,
                                   name='q_next', chkpt_dir=chkpt_dir)
        
        self.default_epsilon = epsilon
        self.last_observation = None
        self.last_reward = 0
        self.last_action = 0

    def store_transition(self, state, action, reward, state_, done):
        self.memory.store_transition(state, action, reward, state_, done)
    
    def get_action(self, observation):
        
        if self.last_observation != None:
            self.store_transition(self.last_observation, self.last_action,
                                   self.last_reward, observation)
            self.learn()
        if np.random.random() > self.epsilon:
            #observation = observation[np.newaxis,:]
            state = T.tensor(observation).to(self.q_eval.device)
            _, advantage = self.q_eval.forward(state)
            action = T.argmax(advantage).item()
        else:
            action = np.random.choice(self.action_space)
        return action
    
    def replace_target_network(self):
        if self.replace_target_cnt is not None and \
           self.learn_step_counter % self.replace_target_cnt == 0:
            self.q_next.load_state_dict(self.q_eval.state_dict())

    def decrement_epsilon(self):
    
        self.epsilon = self.epsilon - self.eps_dec \
                         if self.epsilon > self.eps_min else self.eps_min

    def learn(self):
        if self.memory.mem_cntr < self.batch_size:
            return

        self.q_eval.optimizer.zero_grad()

        self.replace_target_network()

        state, action, reward, new_state, done = \
                                self.memory.sample_buffer(self.batch_size)

        # using T.Tensor seems to reset datatype to float
        # using T.tensor preserves source data type
        state = T.tensor(state).to(self.q_eval.device)
        new_state = T.tensor(new_state).to(self.q_eval.device)
        action = T.tensor(action).to(self.q_eval.device)
        rewards = T.tensor(reward).to(self.q_eval.device)
        dones = T.tensor(done, dtype=T.bool).to(self.q_eval.device)

        V_s, A_s = self.q_eval.forward(state)
        V_s_, A_s_ = self.q_next.forward(new_state)

        q_pred = T.add(V_s, (A_s - A_s.mean(dim=1, keepdim=True))).gather(1,
                                              action.unsqueeze(-1)).squeeze(-1)

        q_next = T.add(V_s_, (A_s_ - A_s_.mean(dim=1, keepdim=True)))
        q_target = rewards + self.gamma*T.max(q_next, dim=1)[0].detach()
        q_target[dones] = 0.0

        loss = self.q_eval.loss(q_target, q_pred).to(self.q_eval.device)
        loss.backward()
        self.q_eval.optimizer.step()
        self.learn_step_counter += 1

        self.decrement_epsilon()

    def save_models(self, name):
        self.q_eval.save_checkpoint(name)
        self.q_next.save_checkpoint(name)

    def load_models(self):
        self.q_eval.load_checkpoint()
        self.q_next.load_checkpoint()

    
    def reset_epsilon(self):
        self.epsilon = self.default_epsilon

    
    def get_skip_action(self, transit_loc_capacity: list, pax_demand: list):
        pass
         

        

class Stop:
    def __init__(self, index: int):
        self.index = index

class Passenger:
    def __init__(self, id: int, board_from: int, alight_to: int, arr_time: time):
        self.id = id
        self.board_from = board_from
        self.alight_to = alight_to
        self.arr_time = arr_time
        self.state = PaxState.TO_BOARD
        self.on_transit_id = -1

class SimulationEvent:
    def __init__(self, id: int, transit: Transit, event_type: EventType):
        self.id = id
        self.transit = transit
        self.event_type = event_type

    '''def execute(self) -> list:
        pass
    

class DispatchEvent(SimulationEvent):
    def __init__(self, id: int, transit: Transit, event_type: EventType):
        super().__init__(id, transit, event_type)
    
    def execute(self) -> list:
        events_to_schedule = []'''
        

        


