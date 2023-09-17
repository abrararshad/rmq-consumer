from shared.models.job import Job
from .base_service import BaseService


class JobService(BaseService):
    files_dir = None
    config = None

    def _initialize(self, data):
        job = Job(self._collection)

        if '_id' not in data:
            return None

        return job.initialize(data)

    def create(self, data):
        event = Job(self._collection, self.config)
        event.save(data)
        return event

    def find_by_hash(self, hash):
        result = self._collection.find_one({"hash": hash})
        if result:
            return self._initialize(result)
        else:
            pass

        return None