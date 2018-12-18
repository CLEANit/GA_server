import numpy as np
import os
import pymongo
from time import sleep
import datetime

if not os.path.exists('./champions'):
    os.makedirs('./champions')

n_gen = 10                          # Number of generations
n_pop = 5                           # Starting population
n_mutate = 2                        # Number of mutations per generation
n_sacrifice = 2                     # Number of removals per generation
load = False                        # Load previous champion (only if not restarting)
load_gen = 0                        # Generation to load
restart = False                     # Restart from last completed generation
wins = 100                          # Wins required for champion to be considered winner
t_max = 60                          # Number of seconds before a policy in the working on table expires 
n_avg = 2                           # Number of times each policy is evaluated
game = 'water-v0'                   # Game the workers will be playing
hidden_units = [1024]               # Number of hidden units for each layer
mut_rate = 0.05                     # Rate used for the mutation process
db_name = 'water'                   # Name of database to use
db_loc = 'coombs.science.uoit.ca'   # Location of MongoDB instance
db_port = 2507                      # Port for MongoDB instance
submit = 'bash -ic "cd ~/submit_scripts/; sbatch submit.sh"'

client = pymongo.MongoClient(db_loc + ':' + str(db_port))
finished_table = client[db_name + '-finished']
unfinished_table = client[db_name + '-unfinished']
working_table = client[db_name + '-working']
backup_table = client[db_name + '-backup']
parameter_table = client['parameters']

delete = parameter_table.posts.delete_many({})
params = {'game': game, 'hidden_units': hidden_units, 'db_name': db_name, 'mut_rate': mut_rate}
insert = parameter_table.posts.insert_one(params)

if not os.path.exists('./champions/' + game):
    os.makedirs('./champions/' + game)

if n_sacrifice > n_mutate:
    n_sacrifice = n_mutate
    print ('Sacrifice > growth per generation. n_sacrifice lowered to ' + str(n_sacrifice))
if n_pop <= 2:
    n_sacrifice = 0
    print ('Not enough population to sacrifice. n_sacrifice lowered to ' + str(n_sacrifice))
elif n_sacrifice >= n_pop - 1:
    n_sacrifice = n_pop - 2
    print ('Sacrifice too large. n_sacrifice lowered to ' + str(n_sacrifice))

population = []
n_backup = backup_table.posts.count_documents({})
if restart and n_backup <= n_pop:
    n_finished = finished_table.posts.count_documents({})
    n_unfinished = unfinished_table.posts.count_documents({})
    n_working = working_table.posts.count_documents({})
    if (n_pop * n_avg) == (n_finished + n_working + n_unfinished):
        print('Restarting from last calculation...')
        policy = finished_table.posts.find_one()
        if policy == None:
            policy = unfinished_table.posts.find_one()
        if policy == None:
            policy = working_table.posts.find_one()
        gen = policy['gen']
    else:
        print('Previous population size does not match current population size.')
        print('Restarting from last back-up...')
        delete = finished_table.posts.delete_many({})
        delete = unfinished_table.posts.delete_many({})
        delete = working_table.posts.delete_many({})
        population = backup_table.posts.find({})
        gen = population[0]['gen']
        name = 0
        for policy in population:
            for i in range(n_avg):
                new_policy = {'_id': policy['_id'], 'gen': gen, 'name': name, 'id': i, 'seeds': policy['seeds']}
                unfinished_table.posts.insert_one(new_policy)
            name += 1
        if n_backup < n_pop:
            for j in range(n_pop - len(population)):
                for i in range(n_avg):
                    new_policy = {'gen': gen, 'name': name, 'id': i, 'seeds': [np.random.randint(int(1e9))]}
                    unfinished_table.posts.insert_one(new_policy)
            name += 1

elif load:
    delete = finished_table.posts.delete_many({})
    delete = unfinished_table.posts.delete_many({})
    delete = working_table.posts.delete_many({})
    delete = backup_table.posts.delete_many({})
    gen = load_gen
    data = np.load('./champions/' + game + '_' + str(gen) + '.npz')
    print('Loading previous champion...')
    for i in range(n_avg):
        new_policy = {'gen': gen, 'name': 0, 'id': i, 'seeds': data['seeds']}
        unfinished_table.posts.insert_one(new_policy)

    name = 1
    for j in range(n_pop - 1):
        for i in range(n_avg):
            new_policy = {'gen': gen, 'name': name, 'id': i, 'seeds': [np.random.randint(int(1e9))]}
            unfinished_table.posts.insert_one(new_policy)
        name += 1

else:
    delete = finished_table.posts.delete_many({})
    delete = unfinished_table.posts.delete_many({})
    delete = working_table.posts.delete_many({})
    delete = backup_table.posts.delete_many({})
    print('Initializing population...')
    gen = 0
    name = 0
    for j in range(n_pop):
        for i in range(n_avg):
            new_policy = {'gen': gen, 'name': name, 'id': i, 'seeds': [np.random.randint(int(1e9))]}
            unfinished_table.posts.insert_one(new_policy)
        name += 1

winning = False
max_score = -10000.0

while not winning:
    for generation in range(n_gen):
        gen += 1

        n_finished = 0
        p_done = 0.0
        p_done0 = -1.0

        while n_finished < (n_pop * n_avg):
            sleep(5)
            n_finished = finished_table.posts.count_documents({})
            p_done = n_finished / (n_pop * n_avg) * 100.0
            if p_done != p_done0:
                print(('%.2f' % p_done) + '% of population is finished.')
            p_done0 = p_done

            n_working = working_table.posts.count_documents({})
            if n_working > 0:
                work_population = working_table.posts.find({})
                for policy in work_population:
                    dt = datetime.datetime.utcnow() - policy['start_time']
                    if dt.seconds > t_max:
                        new_policy = {'_id': policy['_id'], 'gen': policy['gen'], 'name': policy['name'], 'id': policy['id'], 'seeds': policy['seeds']}

                        if n_finished < n_pop:
                            try:
                                insert = unfinished_table.posts.insert_one(new_policy)
                                os.system('ssh fock -t \'bash -ic \"cd ~/submit_scripts/; sbatch submit.sh\"\'')
                            except pymongo.errors.DuplicateKeyError:
                                pass

                        delete = working_table.posts.delete_one(policy)

                        print('Moving expired policy back to unfinished table.')

        population = []
        for i in range(n_pop):
            policies = finished_table.posts.find({'name': i})
            score = 0.0
            _ids = []
            for policy in policies:
                score += policy['score'] / n_avg
                _ids.append(policy['_id'])

            new_policy = {'_ids': _ids, 'gen': policy['gen'], 'name': policy['name'], 'seeds': policy['seeds'], 'score': score}
            population.append(new_policy)

        population = sorted(population, key=lambda k: k['score'])
        population = list(population[n_sacrifice:])
        n_pop -= n_sacrifice
        scores = 0.0
        for policy in population:
            scores += policy['score'] / n_pop

        print('Generation %d: Average Score = %0.4f, Max Score = %0.4f' %(gen, np.mean(scores), population[-1]['score']))

        if max_score < population[-1]['score']:
            champion = population[-1]
            print('Saving this generations champion...')
            np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion['seeds'])
            max_score = champion['score']

        mutants = []
        for i in range(n_mutate):
            r = np.random.randint(n_pop)
            seeds = population[r]['seeds']
            seeds.append(np.random.randint(int(1e9)))
            new_policy = {'gen': gen, 'seeds': seeds}
            mutants.append(new_policy)

        n_pop += n_mutate

        name = 0
        for policy in population:
            new_policy = {'gen': gen, 'name': name, 'seeds': policy['seeds']}
            insert = backup_table.posts.insert_one(new_policy)
            name += 1

        delete = backup_table.posts.delete_many({'gen': gen - 1})

        name = 0
        for policy in population:
            for i in range(n_avg):
                new_policy = {'_id': policy['_ids'][i], 'gen': gen, 'name': name, 'id': i, 'seeds': policy['seeds']}
                insert = unfinished_table.posts.insert_one(new_policy)
                delete = finished_table.posts.delete_one({'_id': policy['_ids'][i]})
                os.system('ssh fock -t \'bash -ic \"cd ~/submit_scripts/; sbatch submit.sh\"\'')
            name += 1

        for policy in mutants:
            for i in range(n_avg):
                new_policy = {'gen': gen, 'name': name, 'id': i, 'seeds': policy['seeds']}
                insert = unfinished_table.posts.insert_one(new_policy)
                os.system('ssh fock -t \'bash -ic \"cd ~/submit_scripts/; sbatch submit.sh\"\'')
            name += 1

        delete = finished_table.posts.delete_many({'gen': gen - 1})

    np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion)

    if max_score > wins:
        winning = True
