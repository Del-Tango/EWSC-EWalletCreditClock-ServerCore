from itertools import count

#   # TODO: Uncalled
#   def check_user_pass_strength(self, user_pass):
#       _values = {'msg': str(), 'verdict': False}
#       _strong_regex = '((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*]).{8,30})'
#       _weak_regex = '((\d*)([a-z]*)([A-Z]*)([!@#$%^&*]*).{8,30})'
#       if len(user_pass) >= 8:
#           if bool(re.match(_strong_regex, user_pass)) == True:
#               _values.update({
#                   'msg': 'The password is strong',
#                   'verdict': True,
#               })
#           elif bool(re.match(_weak_regex, user_pass)) == True:
#               _values.update({
#                   'msg': 'Weak password.',
#                   'verdict': True,
#               })
#       else:
#           _values.update({
#               'msg': 'Invalid password.',
#               'verdict': False,
#           })
#       return _values


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
