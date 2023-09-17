from shared.types import JobStatus
from mongoday.field import BaseField, MongoIDField, StringField, MapField, IntegerField, BooleanField
from mongoday.model import BaseModel

class Job(BaseModel):
    def __init__(self, collection, config=None):
        self.hash = StringField()
        self.cwd = StringField()
        self.command_args = MapField()
        self.executor = StringField()
        self.status = IntegerField(None)
        self.error = StringField()
        self.retry = IntegerField(0)

        indexes = [
            [('hash', 1), {'unique': True}],
            [('user_id', -1)],
            [('command_args', 'text'), ('error', 'text')],
        ]

        self.add_indexes(indexes)

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
        self.error = f"{self.error}\n\n------------------>\n\n{error}" if self.error else error
        self.save()
