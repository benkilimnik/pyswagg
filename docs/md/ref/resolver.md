This module **pyswagr.resolve.Resolver** is provided to customize the way to load OpenAPI spec. For example, you save the swagger.json of petstore (example server provided by OpenAPI team) into memory as dict and would like to use it to create an pyswagr.App instance
```python
from pyswagr import App
from pyswagr.resolve import Resolver
from pyswagr.getter import DictGetter

loaded_sepc # the loaded spec in memory as dict

# prepare the getter
getter = DictGetter([''], {'': loaded_spec})
app = App.load('', resolver=Resolver(default_getter=getter))
app.prepare()
```

For multiple documents specs (ex. Swagger 1.2, or Swagger 2.0 with $ref to external documents), you need to pass all urls/paths to be resolved in the right order to the 1st parameter of DictGetter, which is not a trivial for a normal user and there is no good utility provided in pyswagr, so I don't recommend using **pyswagr.getter.DictGetter** for this case. ex. the wordnik example in Swagger 1.2:
```python
from pyswagr import App
from pyswagr.resolve import Resolver
from pyswagr.getter import DictGetter

# those loaded object in memory
loaded_resource_list
loaded_pet
loaded_user
loaded_store

# prepare the getter, the loaded order should be past in 1st parameter as list
getter = DictGetter([
    '',
    'pet.json',
    'user.json',
    'store.json',
], {
    '': loaded_resource_list,
    'pet.json': pet,
    'store.json': store,
    'user.json': user
})
app = App.load('', resolver=Resolver(default_getter=getter))
app.prepare()
```

