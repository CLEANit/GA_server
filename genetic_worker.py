import numpy as np
import gym
import gym.spaces
from reactive control import rc_gym

class Policy():
    def __init__(self, shape, hidden_units, num_actions, a_bound, seeds):
        self.shape = shape
        self.hidden_units = hidden_units
        self.num_actions = num_actions
        self.a_bound = a_bound
        self.seeds = seeds
        self.W = []
        self.B = []
        seed = seeds[0]
        np.random.seed(seed)
        num_in = self.shape
        num_out = self.hidden_units[0]
        w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
        b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
        self.W.append(w)
        self.B.append(b)
        for i in range(1, self.hidden_units):
            num_in = self.hidden_units[i-1]
            num_out = self.hidden_units[i]
            w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
            b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
            self.W.append(w)
            self.B.append(b)

        num_in = self.hidden_units[-1]
        num_out = self.num_actions
        w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
        b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
        self.W.append(w)
        self.B.append(b)
        for s in range(1, len(seeds)):
            seed = seeds[s]
            np.random.seed(seed)
            num_in = self.shape
            num_out = self.hidden_units[0]
            w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
            b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
            self.W[0] += 0.05 * w
            self.B[0] += 0.05 * b
            for i in range(1, self.hidden_units):
                num_in = self.hidden_units[i-1]
                num_out = self.hidden_units[i]
                w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
                b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
                self.W[i] += 0.05 * w
                self.B[i] += 0.05 * b

            num_in = self.hidden_units[-1]
            num_out = self.num_actions
            w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
            b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
            self.W[-1] += 0.05 * w
            self.B[-1] += 0.05 * b

    def evaluate(self, state):
        Y = np.tanh(np.matmul(state, self.W[i]) + self.B[i])
        for i in range(len(self.W)):
            Y = np.tanh(np.matmul(Y, self.W[i]) + self.B[i])

        Y = (Y + 1.0) / 2.0
        return Y * (self.a_bound[1] - self.a_bound[0]) + self.a_bound[0]

####################################################################
#####                                                          #####
#####         Wait for unfinished policies to be ready         #####
#####    Move the unfinished policy to the inprogress table    #####
#####                                                          #####
####################################################################

game = '2h2o-v0'
env = gym.make(game)
s = env.reset()
shape = s.shape[0]
num_actions = env.action_space.shape[0]
a_bound = [env.action_space.low, env.action_space.high]
policy = Policy(shape, hidden_units, num_actions, a_bound, seeds)
reward = 0
d = False
while not d:
    a = policy.evaluate(s)
    s, r, d, _ = env.step(a)
    reward += r

####################################################################
#####                                                          #####
#####            Populate the finished policy table            #####
#####                                                          #####
####################################################################
