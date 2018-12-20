import numpy as np
import gym
import gym.spaces
from reactive_control import rc_gym
import pymongo
from time import sleep
import datetime
import os

class Policy():
    def __init__(self, shape, hidden_units, num_actions, a_bound, mut_rate, space, seeds):
        self.shape = shape
        self.hidden_units = hidden_units
        self.num_actions = num_actions
        self.a_bound = a_bound
        self.mut_rate = mut_rate
        self.space = space
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
        X = (state - self.space.low) / (self.space.high - self.space.low)
        Y = np.tanh(np.matmul(state, self.W[0]) + self.B[0])
        for i in range(1, len(self.W)):
            Y = np.tanh(np.matmul(Y, self.W[i]) + self.B[i])

        Y = (Y + 1.0) / 2.0
        return Y * (self.a_bound[1] - self.a_bound[0]) + self.a_bound[0]

def work():
    db_loc = 'fock'                     # Location of MongoDB instance
    db_port = 2507                      # Port for MongoDB instance

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                client = pymongo.MongoClient(db_loc + ':' + str(db_port))
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                parameter_table = client['parameters']
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                params = parameter_table.posts.find_one()
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    db_name = params['db_name']         # Name of database to use

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                finished_table = client[db_name + '-finished']
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                unfinished_table = client[db_name + '-unfinished']
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                working_table = client[db_name + '-working']
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    n_delete = 0
    while n_delete < 1:
        n_unfinished = 0
        while n_unfinished < 1:
            sleep(1)
            connected = False
            attempt = 0
            while not connected:
                if attempt < 5:
                    try:
                        n_unfinished = unfinished_table.posts.count_documents({})
                        connected = True
                    except pymongo.errors.AutoReconnect:
                        connected = False
                        attempt += 1
                else:
                    return 0.0

        connected = False
        attempt = 0
        while not connected:
            if attempt < 5:
                try:
                    policy = unfinished_table.posts.find_one()
                    connected = True
                except pymongo.errors.AutoReconnect:
                    connected = False
                    attempt += 1
            else:
                return 0.0

        new_policy = {'_id': policy['_id'], 'gen': policy['gen'], 'name': policy['name'], 'id': policy['id'], 'seeds': policy['seeds'], 'start_time': datetime.datetime.utcnow()}

        try:
            connected = False
            attempt = 0
            while not connected:
                if attempt < 5:
                    try:
                        insert = working_table.posts.insert_one(new_policy)
                        connected = True
                    except pymongo.errors.AutoReconnect:
                        connected = False
                        attempt += 1
                else:
                    return 0.0

        except pymongo.errors.DuplicateKeyError:
            sleep(5)
            try:
                connected = False
                attempt = 0
                while not connected:
                    if attempt < 5:
                        try:
                            insert = working_table.posts.insert_one(new_policy)
                            connected = True
                        except pymongo.errors.AutoReconnect:
                            connected = False
                            attempt += 1
                else:
                    return 0.0

            except pymongo.errors.DuplicateKeyError:
                pass

        connected = False
        attempt = 0
        while not connected:
            if attempt < 5:
                try:
                    delete = unfinished_table.posts.delete_one(policy)
                    connected = True
                except pymongo.errors.AutoReconnect:
                    connected = False
                    attempt += 1
            else:
                return 0.0

        n_delete = delete.deleted_count

    game = params['game']
    env = gym.make(game)
    s = env.reset()
    shape = s.shape[0]
    hidden_units = params['hidden_units']
    num_actions = env.action_space.shape[0]
    a_bound = [env.action_space.low, env.action_space.high]
    mut_rate = params['mut_rate']
    space = env.observation_space
    seeds = policy['seeds']
    policy = Policy(shape, hidden_units, num_actions, a_bound, mut_rate, space, seeds)
    reward = 0
    d = False
    step = 0
    while not d:
        print('Step:', step)
        a = policy.evaluate(s)
        s, r, d, _ = env.step(a)
        reward += r
        step += 1

    finished_policy = {'_id': new_policy['_id'], 'gen': new_policy['gen'], 'name': new_policy['name'], 'id': new_policy['id'], 'seeds': new_policy['seeds'], 'score': reward}

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                insert = finished_table.posts.insert_one(finished_policy)
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    connected = False
    attempt = 0
    while not connected:
        if attempt < 5:
            try:
                delete = working_table.posts.delete_one(new_policy)
                connected = True
            except pymongo.errors.AutoReconnect:
                connected = False
                attempt += 1
        else:
            return 0.0

    print('Policy ' + str(new_policy['name']) + '.' + str(new_policy['id']) + ' has a score of ' + str(reward) + '.')
    return 0.0

while True:
    work()
