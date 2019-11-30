import pysnooper

file = 'test.conf'
log_conf = {
            'log-dir': None,
            'log-debug': None,
            'log-info': None,
            'log-critical': None,
            'log-error': None,
            'log-warning': None,
            }
sys_conf = {'runlvl': None,
            'wallet_id': None,
            'load_demo': None,
            }

def fetch_config_dicts():
    return [log_conf, sys_conf]

def find_config_dict(dict_set, key):
    for item in dict_set:
        if key in item.keys():
            return item
    return False

@pysnooper.snoop()
def set_config_value(dct, key, val):
    if not dct:
        return False
    dct[key] = val
    return dct

@pysnooper.snoop()
def config_file_parser(fl):
    config_dicts = fetch_config_dicts()
    with open(fl, 'r') as config_file:
        lines = config_file.readlines()
        for line in lines:
            key_val = line.split(':')
            dct = find_config_dict(config_dicts, key_val[0])
            set_config_value(dct, key_val[0], str(key_val[1]).strip('\n'))

config_file_parser(file)
print(log_conf)
print(sys_conf)

#   @pysnooper.snoop()
#   def recursive_key_finder(dct, key, depth, count):
#       if depth is not count:
#           return recursive_key_finder(dct[key], key, dept, (count + 1))
#       return dct[key]

#   with open(file, 'r') as conf_file:
#       lines = conf_file.readlines()
#       for line in lines:
#           key_val = line.split(':')
#   #       print(key_val)
#           if len(key_val[0].split('.')) > 1:
#               tree = key_val[0].split('.')
#   #           print(tree)
#               depth = len(tree)
#   #           print(depth)
#               tmp_dct = conf
#               for item in range(0, (depth - 1)):
#                   if item is (depth - 1):
#                       tmp_dct = tmp_dct[tree[item]] = key_val[1].strip('\n')
#                   tmp_dct = tmp_dct[tree[item].strip('\n')]
#                   print(tmp_dct)


#       conf.update({
#           key_val[0].strip('\n'):
#           key_val[1].strip('\n')
#       })

#print(conf)
