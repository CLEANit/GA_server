import numpy as np
import os

if not os.path.exists('./champions'):
    os.makedirs('./champions')

n_gen = 100 # Number of generations
n_pop = 20 # Starting population
n_mutate = 10 # Number of mutations per generation
n_sacrifice = 10 # Number of removals per generation
load = False # Load previous champion
load_gen = 0 # Generation to load
wins = 100 # Wins required for champion to be considered winner

if not os.path.exists('./champions/' + game):
    os.makedirs('./champions/' + game)

name = 0
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
if load == True:
    gen = load_gen
    data = np.load('./champions/' + game + '_' + str(gen) + '.npz')
    hidden_units = data['h']
    population += data['seeds']
    print ('Loading previous champion...')
else:
    gen = 0
    population += [np.random.randint(int(1e9))]

for i in range(n_pop - 1):
    population += [np.random.randint(int(1e9))]

winning = False
max_s0 = -10000.0

while not winning:
    for generation in range(n_gen):
        gen += 1

        ####################################################################
        #####                                                          #####
        #####           Populate the unfinished policy table           #####
        #####         Wait for unfinished policy tale to empty         #####
        #####        Gather finished policies with their scores        #####
        #####            Average the scores for each policy            #####
        #####                                                          #####
        ####################################################################

        l1, l2 = zip(*sorted(zip(scores, population), key = lambda x: x[0]))
        scores = np.array(l1[n_sacrifice:])
        population = list(l2[n_sacrifice:])
        print('Generation %d: Average Score = %0.4f, Max Score = %0.4f' %(gen, np.mean(scores), scores[-1]))
        n_pop -= n_sacrifice

        if max_s0 < scores[-1]:
            champion = population[-1]
            np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion)
            max_s0 = scores[-1]

        choice = np.ones(len(scores))
        mutants = []
        for i in range(n_mutate):
            r = np.random.randint(n_pop)
            new_policy = population[r]
            mutants += new_policy + [np.random.randint(int(1e9))])

        n_pop += n_mutate

        population += mutants

    np.savez('./champions/' + game + '/' + game + '.npz', seeds=champion)

    if max_s0 > wins:
        winning = True
