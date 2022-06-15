## Testing a Local Server

As a backend developer, you will need to test your API before shipping. We provide a simple way to patch the url before client actually making a request. (note: this sample requires [requests](https://github.com/kennethreitz/requests) installed on your environment.)

```python
from pyswagg import App
from pyswagg.contrib.client.request import Client

# create a App with a local resource file
app = App.create('/path/to/your/resource/file/swagger.json')
# init the client
client = Client()

# try to making a request
client.request(
  app.op['getUserByName'](username='Tom'),
  opt=dict(
    url_netloc='localhost:8001' # patch the url of petstore to localhost:8001
  ))
```
