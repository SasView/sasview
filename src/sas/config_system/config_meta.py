
class ConfigLocked(Exception):
    def __init__(self):
        super().__init__(self,
                         "The Config class cannot be subclassed or added to dynamically, see config_system.py for details")


class ConfigMeta(type):
    def __new__(typ, name, bases, classdict):
        for b in bases:
            if isinstance(b, ConfigMeta):
                raise TypeError
        return type.__new__(typ, name, bases, dict(classdict))


class ConfigBase:
    def __init__(self):
        self._locked = False

    def _lock(self):
        self._locked = True

    def save(self):
        #TODO: Implement save functionality to yaml (and load, with schema)
        raise NotImplementedError()

    def __setattr__(self, key, value):
        if hasattr(self, "_locked") and self._locked:
            if key not in self.__dict__:
                raise ConfigLocked()

        super().__setattr__(key, value)