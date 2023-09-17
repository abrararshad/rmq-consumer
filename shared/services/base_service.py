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

    def get(self, id):
        m = self._collection.find_one({"_id": ObjectId(id)})

        if m:
            return self._initialize(m)

        return None

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

    def _initialize(self, data):
        raise NotImplementedError

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
