The initialization of pyswagr starts from **App.\_create_(url)**, where **url** could either be a _url_ or a _file_ path. This function returns a App instance, which would be used to initiate Security.

**App.op** provides a shortcut to access Operation objects, which will produce a set of request/response for SwaggerClient to access API. The way we provide here would help to minimize the possible difference introduced by Swagger2.0 when everything is merged into one file.
```python
# call an API when its nickname is unique
App.op['getPetById']
# call an API when its nickname collid with other resources
App.op['user', 'getById'] # operationId:'getById', tags:'user' (or a user resource in Swagger 1.2)
App.op['pet',  'getById'] # operationId:'getById', tags:'pet'  (or a pet resource in Swagger 1.2)

# utilize App.resolve to do the same thing
App.resolve('#/paths/~1pet~1{petId}').get
# instead of writing JSON-pointers by yourselves, utilize pyswagr.utils.jp_compose
App.resolve(utils.jp_compose('/pet/{petId}', base='#/paths')).get
```
**App.validate(strict=True)** provides validation against the loaded Swagger API definition. When passing _strict=True_, an exception would be raised if validation failed. It returns a list of errors in tuple: _(where, type, msg)_.

**App.resolve(JSON_Reference)** is a new way to access objects. For example, to access a Schema object 'User':
```python
app.resolve('#/definitions/User')
```
This function accepts a [JSON Reference](http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03), which is composed by an url and a [JSON Pointer](http://tools.ietf.org/html/rfc6901), it is the standard way to access a Swagger document. Since a JSON reference contains an url, this means you can access any external document when you need:
```python
app.resolve('http://another_site.com/apis/swagger.json#/definitions/User')
```
`pyswagr` will load that swagger.json, create a new `App`, and group it with the `App` you kept (**app** in code above). Internally, when `pyswagr` encounter some $ref directs to external documents, we just silently handle it in the same way.

**App.dump()** dumps the root object(Swagger Object in 2.0, ResourceList Object in 1.2) into a dict.
