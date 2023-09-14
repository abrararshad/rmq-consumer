from shared.models.event import Event
from bson import ObjectId
from .base_service import BaseService
from flask.signals import Namespace

namespace = Namespace()
flavor_created = namespace.signal('flavor_created')


class EventService(BaseService):
    files_dir = None
    config = None

    def _initialize(self, data):
        return self.initialize(data, Event)

    def create(self, entity_id, entity_type, stream_key):
        event = Event(self._collection, self.config)

        # entity_id is not mongoObjectID then convert it to mongoObjectID
        if not isinstance(entity_id, ObjectId):
            entity_id = ObjectId(entity_id)

        event.add(entity_id=entity_id, entity_type=entity_type, stream_key=stream_key)
        return event

    def get_by_stream_key(self, stream_key):
        result = self._collection.find_one({"stream_key": stream_key})
        if result:
            return self._initialize(result)
        else:
            pass

        return None

    def get_by_entity(self, entity_id, entity_type):
        # entity_id is not mongoObjectID then convert it to mongoObjectID
        if not isinstance(entity_id, ObjectId):
            entity_id = ObjectId(entity_id)

        result = self._collection.find_one({"entity_id": entity_id, "entity_type": entity_type})
        if result:
            return self._initialize(result)
        else:
            pass

        return None
