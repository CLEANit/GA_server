import numpy as np
import os
from pymongo import MongoClient
from time import sleep
import datetime

if not os.path.exists('./champions'):
    os.makedirs('./champions')

n_gen = 100                         # Number of generations
n_pop = 20                          # Starting population
n_mutate = 10                       # Number of mutations per generation
n_sacrifice = 10                    # Number of removals per generation
load = False                        # Load previous champion (only if not restarting)
load_gen = 0                        # Generation to load
restart = False                     # Restart from last completed generation
wins = 100                          # Wins required for champion to be considered winner
t_max = 600                         # Number of seconds before a policy in the working on table expires 
n_avg = 5                           # Number of times each policy is evaluated
db_name = '2h2o'                    # Name of database to use
db_loc = 'coombs.science.uoit.ca'   # Location of MongoDB instance
db_port = 2507                      # Port for MongoDB instance

client = MongoClient(db_loc + ':' + str(db_port))
finished_table = client[db_name + '-finished']
unfinished_table = client[db_name + '-unfinished']
working_table = client[db_name + '-working']
backup_table = client[db_name + '-backup']

if not os.path.exists('./champions/' + game):
    os.makedirs('./champions/' + game)

if n_sacrifice > n_mutate + n_breed:
    n_sacrifice = n_mutate + n_breed
    print ('Sacrifice > growth per generation. n_sacrifice lowered to ' + str(n_sacrifice))
if n_pop <= 2:
    n_sacrifice = 0
    print ('Not enough population to sacrifice. n_sacrifice lowered to ' + str(n_sacrifice))
elif n_sacrifice >= n_pop - 1:
    n_sacrifice = n_pop - 2
    print ('Sacrifice too large. n_sacrifice lowered to ' + str(n_sacrifice))

population = []
if restart:
    prev_pop = backup_table.posts.find()
    gen = prev_pop[0]['gen']
    for policy in prev_pop:
        population.append({'seeds': policy['seeds']})
    if len(population) < n_pop:
        for i in range(n_pop - len(population)):
            population.append({'seeds': [np.random.randint(int(1e9))]})
elif load:
    gen = load_gen
    data = np.load('./champions/' + game + '_' + str(gen) + '.npz')
    population.append(data['seeds'])
    print ('Loading previous champion...')
    for i in range(n_pop - 1):
        population.append({'seeds': [np.random.randint(int(1e9))]})
else:
    gen = 0
    for i in range(n_pop):
        population.append({'seeds': [np.random.randint(int(1e9))]})

winning = False
max_s0 = -10000.0

while not winning:
    for generation in range(n_gen):
        gen += 1

        name = 0
        for policy in population:
            for i in range(n_avg):
                new_policy = {'gen': gen, 'name': name, 'id': i, 'seeds': policy['seeds']}
                unfinished_table.posts.insert_one(new_policy)
            name += 1

        delete = finished_table.posts.delete_many({})

        n_finished = 0
        p_done = 0.0
        while n_finished < (n_pop * n_avg):
            sleep(5)
            p_done0 = p_done
            n_finished = finished_table.posts.count_documents({})
            p_done = n_finished / (n_pop * n_avg) * 100.0
            if p_done != p_done0:
                print(p_done, '% of population is finished.')

            n_working = working_table.posts.count_documents({})
            if n_working > 0:
                work_population = working_table.posts.find()
                for policy in work_population:
                    dt = datetime.datetime.utcnow() - policy['start_time']
                    if dt.seconds > t_max:
                        new_policy = {'gen': policy['gen'], 'name': policy['name'], 'id': policy['id'], 'seeds': policy['seeds']}
                        insert = unfinished_table.posts.insert_one(new_policy)
                        delete = unfinished_table.posts.delete_one(policy)

                        print('Moving expired policy back to unfinished table.')

        population = []
        for i in range(n_pop):
            policies = finished_table.posts.find_many({'name': i})
            score = 0.0
            for policy in policies:
                score += policy['score'] / n_avg

            policy = policies[0]
            new_policy = {'gen': policy['gen'], 'name': policy['name'], 'seeds': policy['seeds'], 'score': score}
            population.append(new_policy)

        population = sorted(population, key=lambda k: k['score'])
        population = list(population[n_sacrifice:])
        n_pop -= n_sacrifice
        scores = 0.0
        for policy in population:
            scores += policy['score'] / n_pop

        print('Generation %d: Average Score = %0.4f, Max Score = %0.4f' %(gen, np.mean(scores), population[-1]['score']))

        if max_s0 < population[-1]['score']:
            champion = population[-1]
            np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion['seeds'])
            max_s0 = champion['score']

        mutants = []
        for i in range(n_mutate):
            r = np.random.randint(n_pop)
            seeds = population[r]['seeds']
            seeds.append(np.random.randint(int(1e9)))
            new_policy = {'gen': gen, 'seeds': seeds}
            mutants.append(new_policy)

        n_pop += n_mutate

        population += mutants

        name = 0
        for policy in population:
            new_policy = {'gen': gen, 'name': name, 'seeds': seeds}
            backup_table.posts.insert_one(new_policy)
            name += 1

    np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion)

    if max_s0 > wins:
        winning = True
