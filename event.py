import traceback

class Event:
    """ A simple event class """
    def __init__(self, name):
        self.handlers = set()
        self.name = name

    def __str__(self):
        handler_str = ', '.join(fn.__qualname__ for fn in self.handlers)
        return f"Event '{self.name}' (handled by {handler_str})"
        
    def __repr__(self):
        return str(self)

    def hook(self, handler):
        """ Register a function as an event handler """
        self.handlers.add(handler)
        return self

    def fire(self, *args, **kwargs):
        """ Fire this event """
        try:
            for handler in self.handlers:
                handler(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()

    def unhook(self, handler):
        """ De-register an event handler from this event. Throws EventError"""
        try:
            self.handlers.remove(handler)
        except:
            raise EventError("Can't unhook handler %s: \
                handler %s does not hook into this event!" % (handler, handler))


class EventError(BaseException):
    """ EventError class - When something goes wrong in an event."""
    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def __str__(self):
        return self.value
