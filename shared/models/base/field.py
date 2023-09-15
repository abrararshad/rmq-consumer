from bson.objectid import ObjectId


class BaseField(object):
    def __init__(self, value=None):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class MongoIDField(BaseField):
    @property
    def value(self):
        if self._value:
            return str(self._value)

        return None

    @value.setter
    def value(self, value):
        if value:
            self._value = ObjectId(value)


class StringField(BaseField):
    @property
    def value(self):
        return str(super().value)

    @value.setter
    def value(self, value):
        if value:
            self._value = str(value)
        else:
            self._value = ''


class IntegerField(BaseField):
    @property
    def value(self):
        v = super().value
        if v:
            return int(v)
        else:
            return 0

    @value.setter
    def value(self, value):
        if value:
            self._value = int(float(value))


class BooleanField(BaseField):
    @property
    def value(self):
        v = super().value
        if v:
            return bool(v)
        else:
            return False

    @value.setter
    def value(self, value):
        if value is not None:
            self._value = bool(value)


class FloatField(BaseField):
    @property
    def value(self):
        v = super().value
        if v:
            return float(v)
        else:
            return 0

    @value.setter
    def value(self, value):
        if value:
            self._value = float(value)


class MapField(BaseField):
    @property
    def value(self):
        v = super().value
        if v:
            return dict(v)
        else:
            return {}

    @value.setter
    def value(self, value):
        if value:
            self._value = dict(value)
