from datetime import datetime
import uuid


class AsDictMixin:
    def as_dict(self, ignored_keys=[]):
        def normalize_value(value):
            if isinstance(value, uuid.UUID):
                return str(value)
            elif isinstance(value, datetime):
                return int(value.timestamp() * 1000)
            return value

        return {
            c.name: normalize_value(getattr(self, c.name))
            for c in self.__table__.columns if c.name not in ignored_keys
        }
