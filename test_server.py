from pymongo import MongoClient
import numpy as np
from time import sleep
import datetime

client = MongoClient('coombs.science.uoit.ca:2507')
db = client['test-database']
db1 = client['test-database1']
db2 = client['test-database2']

delete = db.posts.delete_many({})
delete = db1.posts.delete_many({})
delete = db2.posts.delete_many({})

n_max = 10
t_max = 20

for j in range(n_max):
    policy = {'id': j, 'seeds': [j]}
    insert = db1.posts.insert_one(policy)

print('Initialized population')

while True:
    n_pop = 0
    while n_pop < n_max:
        p_done0 = n_pop / n_max
        n_pop = db.posts.count_documents({})
        sleep(5)
        p_done = n_pop / n_max

        if p_done != p_done0:
            print('Finished population:', p_done * 100.0, '%')

        n_work_pop = db2.posts.count_documents({}) 
        if n_work_pop > 0:
            work_population = db2.posts.find()
            for policy in work_population:
                dt = datetime.datetime.utcnow() - policy['start_time']
                if dt.seconds > t_max:
                    delete = db2.posts.delete_one({'_id': policy['_id']})
                    insert = db1.posts.insert_one({'_id': policy['_id'], 'id': policy['id'], 'seeds': policy['seeds']})

                    print('Moving expired policy from working table back to unfinished table')

    population = db.posts.find()
    delete = db.posts.delete_many({})

    print('Deleting finished population')

    for j in range(n_max):
        policy = {'id': j, 'seeds': [j]}
        insert = db1.posts.insert_one(policy)

    print('Populating unfinished table')
