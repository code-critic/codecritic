#!/bin/python3
# author: Jan Hybs


def convert_db(from_db, to_db):
    from database.mongo import Mongo
    from plucky import plucks
    from processing.statuses import Status

    mongo = Mongo()

    def rename(document, old_name, new_name):
        if old_name in document:
            document[new_name] = document[old_name]
            del document[old_name]
        return document

    def delete(document, old_name):
        if old_name in document:
            del document[old_name]
        return document

    def compute_score(statuses):
        return dict(
            score=sum(plucks(statuses, 'score')),
            scores=[
                len([s.score for s in statuses if s.code == 100]),
                len([s.score for s in statuses if s.code == 101]),
                len([s.score for s in statuses if s.code == 200]),
            ]
        )

    processed_ids = [str(x['_id']) for x in mongo.db.get_collection(to_db).find({}, {'_id': 1})]
    items = mongo.db.get_collection(from_db).find()
    updated = list()

    for item in items:
        # skip already processed items
        if str(item['_id']) in processed_ids:
            continue

        rename(item, 'language', 'lang')
        rename(item, 'tests', 'results')
        delete(item, 'datetime')
        result = item.get('result', {})

        if 'attempt' not in item:
            item['attempt'] = int('{:%Y%H%M%S}'.format(item['_id'].generation_time))

        if item.get('action') == 'solve' and 'score' not in result:
            results = item.get('results', [])
            for r in results:
                if 'score' not in r and 'status' in r:
                    r.update(compute_score([Status[r.get('status')]]))

            statuses = list(map(Status.get, plucks(results, 'status')))
            result.update(compute_score(statuses))

        if 'id' in result:
            if str(result['id']).upper() in ('FINAL RESULT', 'EVALUATION'):
                result['id'] = 'Result'
        updated.append(item)

    if updated:
        ack = mongo.db.get_collection(to_db).insert_many(
            updated
        )

        print(ack)
        print(ack.acknowledged)
        print(len(ack.inserted_ids))


# convert_db('data', 'data-1.0.1')
