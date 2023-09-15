from .base.field import StringField, IntegerField, MapField
from shared.types import JobStatus
from .base.model import BaseModel


class Job(BaseModel):
    def __init__(self, collection, config=None):
        self.hash = StringField()
        self.cwd = StringField()
        self.command_args = MapField()
        self.executor = StringField()
        self.status = IntegerField(None)
        self.error = StringField()
        self.retry = IntegerField(0)

        super(Job, self).__init__(collection, config)

    def add(self, data):
        super().save(data)
        return self

    def attempt(self):
        self.retry += 1
        self.save()

    def success(self):
        self.status = JobStatus.SUCCESS
        self.save()

    def fail(self, error):
        self.status = JobStatus.ERROR
        self.error = error
        self.save()
