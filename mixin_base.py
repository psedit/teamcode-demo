import functools
import inspect
import random

class MixinMeta(type):
    define_empties = ['step', 'end_step']
    def __new__(metacls, name, bases, dct):
        for empty in metacls.define_empties:
            if empty not in dct:
                dct[empty] = lambda *a, **k: None
        return super().__new__(metacls, name, bases, dct)

class MixinBase(metaclass=MixinMeta):
    def __init__(self, *a, **k):
        self.all_supers = AllSuperProxy(self)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        old_init = getattr(cls, '__init__', lambda *a, **b: None)
        
        def new_init(self, *a, **kwa):
            if type(self) == cls:
                # We are the most derived type.
                for supercls in cls.mro()[1:]:
                    supercls.__init__(self, *a, **kwa)
                    
                    if (supercls == MixinBase):
                        break
            
            old_init(self, *a, **kwa)
            
        cls._step_mro = cls.mro()[1:-2]
        cls.__init__ = new_init
    
    def all_super_step(self, *args, **kwargs):
        for cls in self._step_mro:
            cls.step(self, *args, **kwargs)
            
    def all_super_end_step(self, *args, **kwargs):
        for cls in self._step_mro:
            cls.end_step(self, *args, **kwargs)

class AllSuperProxy:
    def __init__(self, obj):
        self.cls = type(obj)
        self.obj = obj
    
    @functools.lru_cache()
    def __getattr__(self, f_name):
        return MultiFnProxy(self.obj, self.cls.mro()[1:], f_name)

class MultiFnProxy:
    def __init__(self, obj, superclasses, f_name):
        self.obj = obj
        self.superclasses = superclasses
        self.f_name = f_name
        
        self.supermethods = []
        for superclass in self.superclasses:
            try:
                self.supermethods.append(getattr(superclass, f_name))
            except AttributeError:
                pass
        
        
    def __call__(self, *args, **kwargs):
        return [supermethod(self.obj, *args, **kwargs) for supermethod in self.supermethods]