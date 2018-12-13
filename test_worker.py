from pymongo import MongoClient
import numpy as np
from time import sleep
import datetime

client = MongoClient('coombs.science.uoit.ca:2507')
db = client['test-database']
db1 = client['test-database1']
db2 = client['test-database2']

n_max = 10

j = 0
while True:
    n_pop = 0
    while n_pop < 1:
        n_pop = db1.posts.count_documents({})
        sleep(5)

    n_delete = 0
    while n_delete < 1:
        policy = db1.posts.find_one()
        delete = db1.posts.delete_one({'_id': policy['_id']})
        n_delete = delete.deleted_count

    print('Deleting policy from unfinished table')

    policy = {'_id': policy['_id'], 'id': policy['id'], 'seeds': policy['seeds'], 'start_time': datetime.datetime.utcnow()}
    db2.posts.insert_one(policy)

    print('Adding policy to working table')

    for i in range(5):
        print('Working on step', i+1)
        sleep(1)

    print('Deleting policy from working table')

    policy = db2.posts.find_one({'_id': policy['_id']})
    delete = db2.posts.delete_one({'_id': policy['_id']})

    policy = {'_id': policy['_id'], 'id': policy['id'], 'seeds': policy['seeds'], 'score': j}
    db.posts.insert_one(policy)

    print('Adding policy to finished table')

    j = (j - 1) % n_max
