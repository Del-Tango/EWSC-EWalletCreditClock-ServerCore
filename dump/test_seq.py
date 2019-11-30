from itertools import count


class IDAssigner(object):
    def __init__(self):
        self._next_id = count()

    def __call__(self, klass, *args, **kwargs):
        obj = klass(*args, **kwargs)
        setattr(obj, 'id', next(self._next_id))
        return obj


class Foo(object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


create = IDAssigner()
foo_1 = create(Foo, 'Hello')
foo_2 = create(Foo, 'World')
print(foo_1, foo_1.id)
print(foo_2, foo_2.id)
