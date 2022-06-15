from __future__ import absolute_import
from tornado import web, testing
from tornado.ioloop import IOLoop
from pyswag import App
from pyswag.contrib.client.tornado import TornadoClient
from ...utils import create_pet_db, get_test_data_folder, pet_Mary
import json
import six
import os


sapp = App._create_(get_test_data_folder(version='1.2', which='wordnik'))
received_file = None
received_meta = None
received_headers = None

""" refer to pyswag.tests.data.v1_2.wordnik for details """

class RESTHandler(web.RequestHandler):
    """ base implementation of RequestHandler,
    accept a db as init paramaeter.
    """
    def initialize(self, db):
        self.db = db

    def prepare(self):
        """
        According to FAQ of tornado, they won't handle json media-type.
        """
        super(RESTHandler, self).prepare()

        content_type = self.request.headers.get('Content-Type')
        if content_type and content_type.startswith('application/json'):
            # handle media-type: json
            if content_type.rfind('charset=UTF-8'):
                self.json_args = json.loads(self.request.body.decode('utf-8'))
            else:
                raise web.HTTPError('unsupported application type:' + content_type)


class PetRequestHandler(RESTHandler):
    """ refer to /pet """
    def put(self):
        global received_headers
        received_headers = self.request.headers

        pet = self.json_args
        if not isinstance(pet['id'], int):
            self.set_status(400)
        if not self.db.update_(**pet):
            self.set_status(404)
        else:
            self.set_status(200)
        self.finish()

    def post(self):
        pet = self.json_args
        if self.db.read_(pet['id']) != None:
            self.set_status(409)
        else:
            self.db.create_(**pet)
            self.set_status(200)
        self.finish()


class PetIdRequestHandler(RESTHandler):
    """ refer to /pet/{petId} """
    def delete(self, id):
        if not self.db.delete_(int(id)):
            self.set_status(400)
        self.finish()

    def get(self, id):
        pet = self.db.read_(int(id))
        if not pet:
            self.set_status(404)
        else:
            self.write(json.dumps(pet))
        self.finish()


class ImageRequestHandler(web.RequestHandler):
    """ test for file upload """

    def post(self):
        """ pass additionalMetadata and file to global
        variables.
        """
        global received_file
        global received_meta

        received_file = self.request.files['file'][0].body
        received_meta = self.get_argument('additionalMetadata')

received_files = None

class ImagesUploadRequestHandler(web.RequestHandler):
    """ test for multiple file upload """

    def post(self):
        global received_files

        received_files = self.request.files['images']


""" global variables """

pet_db = create_pet_db()
app = web.Application([
    (r'/api/pet', PetRequestHandler, dict(db=pet_db)),
    (r'/api/pet/(\d+)', PetIdRequestHandler, dict(db=pet_db)),
    (r'/api/pet/uploadImage', ImageRequestHandler),
    (r'/upload', ImagesUploadRequestHandler)
], debug=True)


class TornadoTestCase(testing.AsyncHTTPTestCase):
    """
    """
    def setUp(self):
        global received_file
        global received_meta

        # reset global
        received_file = received_meta = None

        super(TornadoTestCase, self).setUp()
        self.client = TornadoClient()


    def get_new_ioloop(self):
        return IOLoop.instance()

    def get_app(self):
        global app
        return app

    @testing.gen_test
    def test_updatePet(self):
        """ updatePet """
        global pet_db
        resp = yield self.client.request(
            sapp.op['updatePet'](body=dict(id=1, name='Tom1')),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')

    @testing.gen_test
    def test_reuse_req_and_resp(self):
        """ make sure reusing (req, resp) is fine """
        global pet_db
        cache = sapp.op['updatePet'](body=dict(id=1, name='Tom1'))
        resp = yield self.client.request(
            cache,
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))
        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')
        resp = yield self.client.request(
            cache,
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))
        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')

    @testing.gen_test
    def test_addPet(self):
        """ addPet """
        global pet_db

        resp = yield self.client.request(
            sapp.op['addPet'](body=dict(id=5, name='Mission')),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(5)['name'], 'Mission')

    @testing.gen_test
    def test_deletePet(self):
        """ deletePet """
        resp = yield self.client.request(
            sapp.op['deletePet'](petId=5),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(5), None)

    @testing.gen_test
    def test_getPetById(self):
        """ getPetById """
        resp = yield self.client.request(
            sapp.op['getPetById'](petId=2),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.data, pet_Mary)

    @testing.gen_test
    def test_uploadFile(self):
        """ uploadFile """
        global received_file
        global received_meta

        resp = yield self.client.request(
            sapp.op['uploadFile'](
                additionalMetadata='a test file', file=dict(data=six.StringIO('a test Content'), filename='test.txt')),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            ))

        self.assertEqual(resp.status, 200)
        self.assertEqual(received_file.decode(), 'a test Content')
        self.assertEqual(received_meta, 'a test file')

    @testing.gen_test
    def test_uploadImages(self):
        """ test for uploading multiple files """
        global received_files

        app = App._create_(get_test_data_folder(version='2.0', which=os.path.join('io', 'files')))
        resp = yield self.client.request(
            app.op['upload_images'](images=[
                dict(data=six.BytesIO(six.b('test image 1')), filename='_1.k'),
                dict(data=six.BytesIO(six.b('test image 2')), filename='_2.k'),
                dict(data=six.BytesIO(six.b('test image 3')), filename='_3.k'),
            ]),
            opt=dict(
                url_netloc='localhost:'+str(self.get_http_port())
            )
        )

        self.assertEqual(received_files[0], {'body': six.b('test image 1'), 'content_type': 'application/unknown', 'filename': u'_1.k'})
        self.assertEqual(received_files[1], {'body': six.b('test image 2'), 'content_type': 'application/unknown', 'filename': u'_2.k'})
        self.assertEqual(received_files[2], {'body': six.b('test image 3'), 'content_type': 'application/unknown', 'filename': u'_3.k'})

    @testing.gen_test
    def test_custom_headers(self):
        """ test customized headers """
        global received_headers

        yield self.client.request(
            sapp.op['updatePet'](
                body=dict(id=1, name='Tom1')),
                opt=dict(
                    url_netloc='localhost:'+str(self.get_http_port())
                ),
                headers={'X-TEST-HEADER': 'aaa'}
            )

        self.assertEqual(received_headers['X-TEST-HEADER'], 'aaa')

    @testing.gen_test
    def test_custom_headers_multiple_values_to_one_key(self):
        """ test customized headers with multiple values to one key """
        global received_headers

        yield self.client.request(
            sapp.op['updatePet'](
                body=dict(id=1, name='Tom1')),
                opt=dict(
                    url_netloc='localhost:'+str(self.get_http_port()),
                ),
                headers=[('X-TEST-HEADER', 'aaa'), ('X-TEST-HEADER', 'bbb')]
            )

        self.assertEqual(received_headers.get_list('X-TEST-HEADER'), ['aaa', 'bbb'])

