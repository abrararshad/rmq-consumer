from bson.objectid import ObjectId
import pydevd_pycharm


# pydevd_pycharm.settrace('host.docker.internal', port=21000, stdoutToServer=True, stderrToServer=True)


class BaseService:
    config = None

    def __init__(self, app, collection):
        self._app = app
        self._collection = collection

        self.setup_configs()

    def setup_configs(self):
        self.config = self._app.config

    def update(self, find={}, update={}):
        bulk = self._collection.initialize_unordered_bulk_op()
        bulk.find(find).update(update)

        return bulk.execute()

    def find(self, find={}, *opts):
        try:
            sort = None
            limit = None

            i = iter(opts)
            try:
                sort = next(i),
            except Exception as e:
                pass

            try:
                limit = next(i)
            except Exception as e:
                pass

            if sort:
                if limit:
                    result = self._collection.find(find).sort(sort).limit(limit)
                else:
                    result = self._collection.find(find).sort(sort)
            else:
                if limit:
                    result = self._collection.find(find).limit(limit)
                else:
                    result = self._collection.find(find)

            if not result:
                return None

            result = list(result)

            entries = []
            if not result:
                return entries

            for r in result:
                entries.append(self._initialize(r))

            return entries

        except Exception as e:
            raise Exception("Error:{}".format(e))

    def get_count(self, find={}):
        try:
            return self._collection.count_documents(find)
        except Exception as e:
            raise Exception("Count Error: {}".format(e))

    def find_one(self, find=None):
        try:
            if not find:
                return None

            result = self._collection.find_one(find)
            if result:
                return self._initialize(result)
            else:
                return None
        except Exception as e:
            raise Exception('Error: {}'.format(e))

    def aggregate(self, pipelines):
        try:
            return self._collection.aggregate(pipelines)
        except Exception as e:
            return e

    def initialize(self, data, model):
        m = model(self._collection, self.config)

        if data and '_id' not in data:
            return None

        return m.initialize(data)

    def get(self, _id):
        if not _id:
            return None

        result = self._collection.find_one({"_id": ObjectId(str(_id))})
        if result:
            return self._initialize(result)

        return None

    @classmethod
    def mongo_id(cls, _id):
        return ObjectId(_id)
