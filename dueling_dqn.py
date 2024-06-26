import os
import torch as T
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import datetime
#from model_to_onnx import WrapperNet


class ReplayBuffer(object):
    def __init__(self, max_size, input_shape, n_actions):
        self.mem_size = max_size
        self.mem_cntr = 0
        self.state_memory = np.zeros((self.mem_size, *input_shape), dtype=np.float32)
        self.new_state_memory = np.zeros((self.mem_size, *input_shape), dtype=np.float32)
        self.action_memory = np.zeros(self.mem_size, dtype=np.int64)
        self.reward_memory = np.zeros(self.mem_size, dtype=np.float32)
        self.terminal_memory = np.zeros(self.mem_size, dtype=np.uint8)

    def store_transition(self, state, action, reward, state_, done):
        index = self.mem_cntr % self.mem_size
        self.state_memory[index] = state
        self.new_state_memory[index] = state_
        self.action_memory[index] = action
        self.reward_memory[index] = reward
        self.terminal_memory[index] = done
        self.mem_cntr += 1

    def sample_buffer(self, batch_size):
        max_mem = min(self.mem_cntr, self.mem_size)
        batch = np.random.choice(max_mem, batch_size, replace=False)

        states = self.state_memory[batch]
        actions = self.action_memory[batch]
        rewards = self.reward_memory[batch]
        states_ = self.new_state_memory[batch]
        terminal = self.terminal_memory[batch]

        return states, actions, rewards, states_, terminal


class DuelingLinearDeepQNetwork(nn.Module):
    def __init__(self, ALPHA, n_actions, name, input_dims, chkpt_dir='models'):
        super(DuelingLinearDeepQNetwork, self).__init__()

        self.fc1 = nn.Linear(*input_dims, 256)
        self.fc2 = nn.Linear(256, 256)
        self.V = nn.Linear(256, 1)
        self.A = nn.Linear(256, n_actions)
        self.input_dims = input_dims
        self.num_actions = n_actions
        self.optimizer = optim.Adam(self.parameters(), lr=ALPHA)
        self.loss = nn.MSELoss()
        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu')
        print(self.device)
        self.to(self.device)
        self.checkpoint_dir = chkpt_dir
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name+'_dqn')

    def forward(self, state):
        state = state.float()
        l1 = F.relu(self.fc1(state))
        l2 = F.relu(self.fc2(l1))
        V = self.V(l2)
        A = self.A(l2)

        return V, A

    def save_checkpoint(self, name):
        print('... saving checkpoint ...')
        T.save(self.state_dict(), self.checkpoint_file+"_"+name)

    def load_checkpoint(self, name):
        print('... loading checkpoint ...')
        self.load_state_dict(T.load(self.checkpoint_file+"_"+name))
    
    '''def save_as_onnx(self):
        print('... saving onnx ...')
        torch_input = T.randn((1,*self.input_dims)).to(self.device)
        T.onnx.export(
            WrapperNet(self, [self.num_actions], True),
            # A tuple with an example of the input tensors
            (torch_input, T.ones(1, self.num_actions).to(self.device)),
            self.checkpoint_file + ".onnx",
            opset_version=9,
            # input_names must correspond to the WrapperNet forward parameters
            # obs will be obs_0, obs_1, etc.
            input_names=["obs_0", "action_masks"],
            # output_names must correspond to the return tuple of the WrapperNet
            # forward function.
            output_names=["discrete_actions", "discrete_action_output_shape",
                        "version_number", "memory_size"],
            # All inputs and outputs should have their 0th dimension be designated
            # as 'batch'
            dynamic_axes={'obs_0': {0: 'batch'},
                        'action_masks': {0: 'batch'},
                        'discrete_actions': {0: 'batch'},
                        'discrete_action_output_shape': {0: 'batch'}
                        }
        )'''
class Agent(object):
    def __init__(self, gamma, epsilon, alpha, n_actions, input_dims,
                 mem_size, batch_size, eps_min=0.01, eps_dec=5e-7,
                 replace=1000, chkpt_dir='models'):
        self.gamma = gamma
        self.epsilon = epsilon
        self.eps_min = eps_min
        self.eps_dec = eps_dec
        self.action_space = [i for i in range(n_actions)]
        self.learn_step_counter = 0
        self.batch_size = batch_size
        self.replace_target_cnt = replace
        self.memory = ReplayBuffer(mem_size, input_dims, n_actions)

        self.q_eval = DuelingLinearDeepQNetwork(alpha, n_actions, input_dims=input_dims,
                                   name='q_eval', chkpt_dir=chkpt_dir)
        self.q_next = DuelingLinearDeepQNetwork(alpha, n_actions, input_dims=input_dims,
                                   name='q_next', chkpt_dir=chkpt_dir)
        
        self.default_epsilon = epsilon

    def store_transition(self, state, action, reward, state_, done):
        self.memory.store_transition(state, action, reward, state_, done)

    def choose_action(self, observation):
        if np.random.random() > self.epsilon:
            observation = observation[np.newaxis,:]
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
        print("Decrementing Epsilon")
        self.epsilon = self.epsilon - self.eps_dec \
                         if self.epsilon > self.eps_min else self.eps_min
        print("Decrementing Epsilon to", self.epsilon)

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

    def save_models(self):
        self.q_eval.save_checkpoint()
        self.q_next.save_checkpoint()

    def load_models(self):
        self.q_eval.load_checkpoint()
        self.q_next.load_checkpoint()

    def save_onnx(self):
        self.q_eval.save_as_onnx()
    
    def reset_epsilon(self):
        self.epsilon = self.default_epsilon