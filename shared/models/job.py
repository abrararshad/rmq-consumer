from .base.field import StringField, IntegerField
from shared.types import JobStatus
from .base.model import BaseModel


class Job(BaseModel):
    def __init__(self, collection, config=None):
        self.cmd_hash = StringField()
        self.command = StringField()
        self.status = IntegerField(JobStatus.SUCCESS)
        self.error = StringField()
        self.retry = IntegerField(0)

        super(Job, self).__init__(collection, config)

    def add(self, data):
        super().save(data)
        return self
