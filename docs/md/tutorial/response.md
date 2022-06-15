## Access the Response
The return value of 'request' function of each client implementation is a pyswagr.io.Response object.
You need to access the result of your request via its interface (note: this sample requires [requests](https://github.com/kennethreitz/requests) ready on your environment)

```python
from pyswagr import App
from pyswagr.contrib.client.requests import Client

app = App.create('/path/to/your/resource/file/swagger.json')
client = Client()

# making a request
resp = client.request(app.op['getUserByName'](username='Tom'))

# Status
assert resp.status == 200

# Data
# it should return a data accord with '#/definitions/User' Schema object
assert resp.data.id == 1
assert resp.data.username == 'Tom'
# Raw
assert resp.raw == '{"id": 1, "username": "Tom"}'

# To disable parsing of body parameter, and handle 'raw' on your own.
resp.raw_body_only = True
assert resp.data == None

# Header
# header is a dict, its values are lists of values,
# because keys in HTTP header allow duplication.
#
# when the input header is:
# A: 1,
# A: 2,
# B, 1
assert sorted(resp.header['A']) == [1, 2]
assert resp.header['B'] == [1]
```
