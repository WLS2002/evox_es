import chex
import jax
import types

def jit(func):
    return jax.jit(func, static_argnums=(0,))

def use_state(func):
    def wrapper(self, state, *args, **kargs):
        if self.name == '_top_level':
            return func(self, state, *args, **kargs)
        else:
            return_value = func(self, state[self.name], *args, **kargs)
            if isinstance(return_value, tuple):
                state |= {
                    self.name: return_value[0]
                }
                return state, return_value[1:]
            else:
                return state | {
                    self.name: return_value
                }
    return wrapper

def use_state_class(cls, ignore=['setup', 'init', '__init__'], ignore_prefix='_'):
    for attr_name in dir(cls):
        if attr_name.startswith(ignore_prefix):
            continue
        if attr_name in ignore:
            continue

        attr = getattr(cls, attr_name)
        if isinstance(attr, types.FunctionType):
            print(f"wrapped: {attr_name}")
            wrapped = use_state(attr)
            setattr(cls, attr_name, wrapped)
    return cls

class Module:
    def setup(self, key: chex.PRNGKey = None):
        pass

    def init(self, key: chex.PRNGKey = None, name='_top_level'):
        self.name = name
        state = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Module):
                key, subkey = jax.random.split(key)
                submodule_name = f'_submodule_{attr_name}'
                state[submodule_name] = attr.init(subkey, submodule_name)
        return self.setup(key) | state