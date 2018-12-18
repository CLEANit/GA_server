import numpy as np
import gym
import gym.spaces
from reactive_control import rc_gym
import pymongo
from time import sleep
import datetime

class Policy():
    def __init__(self, shape, hidden_units, num_actions, a_bound, mut_rate, seeds):
        self.shape = shape
        self.hidden_units = hidden_units
        self.num_actions = num_actions
        self.a_bound = a_bound
        self.mut_rate = mut_rate
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

        for i in range(1, len(self.hidden_units)):
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
            self.W[0] += mut_rate * w
            self.B[0] += mut_rate * b

            for i in range(1, len(self.hidden_units)):
                num_in = self.hidden_units[i-1]
                num_out = self.hidden_units[i]
                w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
                b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
                self.W[i] += mut_rate * w
                self.B[i] += mut_rate * b

            num_in = self.hidden_units[-1]
            num_out = self.num_actions
            w = np.random.normal(scale = 1.0/(num_in*num_out), size = (num_in, num_out))
            b = np.random.normal(scale = 1.0/(num_in*num_out), size = num_out)
            self.W[-1] += mut_rate * w
            self.B[-1] += mut_rate * b

    def evaluate(self, state):
        Y = np.tanh(np.matmul(state, self.W[0]) + self.B[0])
        for i in range(1, len(self.W)):
            Y = np.tanh(np.matmul(Y, self.W[i]) + self.B[i])

        Y = (Y + 1.0) / 2.0
        return Y * (self.a_bound[1] - self.a_bound[0]) + self.a_bound[0]

db_loc = 'coombs.science.uoit.ca'   # Location of MongoDB instance
db_port = 2507                      # Port for MongoDB instance

client = pymongo.MongoClient(db_loc + ':' + str(db_port))
parameter_table = client['parameters']

params = parameter_table.posts.find_one()
db_name = params['db_name']         # Name of database to use

finished_table = client[db_name + '-finished']
unfinished_table = client[db_name + '-unfinished']
working_table = client[db_name + '-working']

while True:
    n_delete = 0
    while n_delete < 1:
        n_unfinished = 0
        while n_unfinished < 1:
            sleep(1)
            n_unfinished = unfinished_table.posts.count_documents({})

        policy = unfinished_table.posts.find_one()
        new_policy = {'_id': policy['_id'], 'gen': policy['gen'], 'name': policy['name'], 'id': policy['id'], 'seeds': policy['seeds'], 'start_time': datetime.datetime.utcnow()}

        try:
            insert = working_table.posts.insert_one(new_policy)
        except pymongo.errors.DuplicateKeyError:
            sleep(5)
            try:
                insert = working_table.posts.insert_one(new_policy)
            except pymongo.errors.DuplicateKeyError:
                pass

        print('Policy added')
        sleep(5)
        delete = unfinished_table.posts.delete_one(policy)
        n_delete = delete.deleted_count

    game = params['game']
    env = gym.make(game)
    s = env.reset()
    shape = s.shape[0]
    hidden_units = params['hidden_units']
    num_actions = env.action_space.shape[0]
    a_bound = [env.action_space.low, env.action_space.high]
    mut_rate = params['mut_rate']
    seeds = policy['seeds']
    policy = Policy(shape, hidden_units, num_actions, a_bound, mut_rate, seeds)
    reward = 0
    d = False
    while not d:
        a = policy.evaluate(s)
        s, r, d, _ = env.step(a)
        reward += r

    finished_policy = {'_id': new_policy['_id'], 'gen': new_policy['gen'], 'name': new_policy['name'], 'id': new_policy['id'], 'seeds': new_policy['seeds'], 'score': reward}
    insert = finished_table.posts.insert_one(finished_policy)
    delete = working_table.posts.delete_one(new_policy)
