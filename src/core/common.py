import json
import pickle
import yaml

from collections.abc import MutableMapping

# ------------------------- #

class DotDict(dict):
    """Dot notation access to dictionary elements"""
    
    def __getattr__(self, attr, *args):
        if attr.startswith('__'):
            raise AttributeError
            
        val = dict.get(self, attr, *args)
        return DotDict(val) if type(val) is dict else val

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

# ------------------------- #

def write_pkl(obj: object, path: str) -> None:
     with open(path, 'wb') as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)

# ------------------------- #

def read_pkl(path: str) -> object:
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    return data

# ------------------------- #

def write_json(obj: object, path: str) -> None:
    with open(path, 'w') as f:
        json.dump(obj, f)

# ------------------------- #

def read_json(path: str) -> object:
    with open(path, 'r') as f:
        res = json.load(f)
    
    return res

# ------------------------- #

def read_yaml(path: str) -> DotDict:
    with open(path, 'r') as stream:
        f = yaml.safe_load(stream)
    
    f = DotDict(f)

    return f

# ------------------------- #

def flatten(d, parent_key='', sep='_'):

    items = []

    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)