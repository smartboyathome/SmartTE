from pydispatch import dispatcher
from collections import deque, UserDict

'''
These are a collection the custom collections which are used in SmartTE. They
are more specialized versions of collections that already exist in Python.
'''

class OneToOneDict(UserDict):
    '''
        This is just a dict that keeps a one-to-one relationship between each
        key and value. This just means that the data is stored twice in the
        dict, with the original key acting as a key and the original value
        acting as another key.
    '''
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if isinstance(value, (list, tuple)):
            for v in value:
                super().__setitem__(v, key)
        elif isinstance(value, dict):
            for v in value.values():
                super().__setitem__(v, key)
        else:
            super().__setitem__(value, key)

class MaxLengthEventSignallingDeque(deque):
    '''
    This is a special version of the deque. It implements a maximum size by
    popping the last entry off the opposite end of the deque that is being
    added to. In addition, it implements event signalling, sending a signal via
    pydispatch to the specified EmptySignal when it has become empty and
    NoLongerEmptySignal when it has stopped being empty.
    '''

    def __init__(self, MaxSize, EmptySignal, NoLongerEmptySignal, ChangedSignal, PopFromRight=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.EmptySignal = EmptySignal
        self.NoLongerEmptySignal = NoLongerEmptySignal
        self.ChangedSignal = ChangedSignal
        self.MaxSize = MaxSize
        if self.__len__() > 0:
            popfunc = super().pop if PopFromRight else super().popleft
            self.__shrinkIfTooBig(popfunc)
            dispatcher.send(signal=self.NoLongerEmptySignal, sender=self)
        else:
            dispatcher.send(signal=self.EmptySignal, sender=self)
    
    def __isTooLarge(self):
        return self.__len__() > self.MaxSize
    
    def __shrinkIfTooBig(self, popfunc):
        while self.__isTooLarge():
            popfunc()
    
    def __protoPop(self, popFunc):
        was_not_empty = self.__len__() != 0
        return_value = popFunc()
        is_empty_now = self.__len__() == 0
        if was_not_empty and is_empty_now:
            dispatcher.send(signal=self.EmptySignal, sender=self)
        return return_value
    
    def __protoAppend(self, x, appendFunc, popfunc):
        was_empty = self.__len__() == 0
        appendFunc(x)
        not_empty_now = self.__len__() != 0
        if was_empty and not_empty_now:
            dispatcher.send(signal=self.NoLongerEmptySignal, sender=self)
        self.__shrinkIfTooBig(popfunc)

    def __protoRemove(self, x, removeFunc):
        was_not_empty = self.__len__() != 0
        removeFunc(x)
        is_empty_now = self.__len__() == 0
        if was_not_empty and is_empty_now:
            dispatcher.send(signal=self.EmptySignal, sender=self)

    def __changeWrapper(self, function, *args, **kwargs):
        before_length = self.__len__()
        return_value = function(*args, **kwargs)
        after_length = self.__len__()
        if before_length != after_length:
            dispatcher.send(signal=self.ChangedSignal, sender=self)
        return return_value

    def append(self, x):
        self.__changeWrapper(self.__protoAppend, x, super().append, super().popleft)
    
    def appendleft(self, x):
        self.__changeWrapper(self.__protoAppend, x, super().appendleft, super().pop)
    
    def extend(self, x):
        self.__changeWrapper(self.__protoAppend, x, super().extend, super().popleft)
    
    def extendleft(self, x):
        self.__changeWrapper(self.__protoAppend, x, super().extendleft, super().pop)

    def pop(self):
        return self.__changeWrapper(self.__protoPop, super().pop)
    
    def popleft(self):
        return self.__changeWrapper(self.__protoPop, super().popleft)

    def remove(self, x):
        self.__changeWrapper(self.__protoRemove, x=x, removeFunc=super().remove)

    def clear(self):
        self.__changeWrapper(self.__protoPop, super().clear)
