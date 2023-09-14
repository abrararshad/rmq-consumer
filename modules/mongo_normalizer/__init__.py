from bson.json_util import dumps
from json import loads as json_loads


class MongoNormalizer:

    @staticmethod
    def deserialize(data):
        records = json_loads((dumps(data)))

        return_single = False
        if not isinstance(records, list):
            return_single = True
            records = [records]

        # for l in records:
        #     if l['_id']['$oid']:
        #         l['_id'] = l['_id']['$oid']

        for l in records:
            for lr in list(l):
                if isinstance(l[lr], dict):
                    if '$oid' in l[lr]:
                        l[lr] = l[lr]['$oid']

        return records[0] if return_single else records

    def deserialize_new(data):
        records = json_loads((dumps(data)))

        return_single = False
        if not isinstance(records, list):
            return_single = True
            records = [records]

        for l in records:
            if l['_id']['$oid']:
                l['id'] = l['_id']['$oid']

        return records[0] if return_single else records
