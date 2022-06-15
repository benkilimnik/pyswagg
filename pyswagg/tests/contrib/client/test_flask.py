from __future__ import absolute_import
from pyswagg import App
from pyswagg.contrib.client.flask import FlaskTestClient
from ...utils import create_pet_db, get_test_data_folder, pet_Mary
from flask import Flask, json, request
import unittest
import six
import os


sapp = App._create_(get_test_data_folder(version='1.2', which='wordnik'))
pet_db = create_pet_db()
received_file = None
received_meta = None
received_headers = None

#
# a minimum flask application for pet-store example
#
fapp = Flask(__name__)

@fapp.route('/api/pet', methods=['POST', 'PUT'])
def pet():
    if request.method == 'POST':
        if pet_db.read_(request.json['id']) != None:
            return "", 409
        else:
            pet_db.create_(**request.json)
            return "", 200
    elif request.method == 'PUT':
        global received_headers

        received_headers = request.headers
        if not isinstance(request.json['id'], int):
            return "", 400
        if not pet_db.update_(**request.json):
            return "", 404
        else:
            return "", 200

@fapp.route('/api/pet/<int:pet_id>', methods=['DELETE', 'GET'])
def pet_id(pet_id):
    if request.method == 'DELETE':
        if not pet_db.delete_(int(pet_id)):
            return "", 400
        return "", 200
    elif request.method == 'GET':
        pet = pet_db.read_(int(pet_id))
        if not pet:
            return "", 404
        else:
            return json.jsonify(pet), 200

@fapp.route('/api/pet/uploadImage', methods=['POST'])
def pet_image():
    if request.method == 'POST':
        global received_file
        global received_meta

        out = six.BytesIO()
        request.files['file'].save(out)
        received_file = out.getvalue()
        out.close()
        received_meta = request.form['additionalMetadata']

        return "", 200

received_files = None
received_file_names = None

@fapp.route('/upload', methods=['POST'])
def upload_images():
    global received_files
    global received_file_names

    images = request.files.getlist('images')
    received_files = images
    return "", 200

#
# test case
#
class FlaskTestCase(unittest.TestCase):
    """
    """
    @classmethod
    def setUpClass(kls):
        kls.client = FlaskTestClient(fapp.test_client())

    def test_updatePet(self):
        """ updatePet """
        global pet_db
        resp = self.client.request(
            sapp.op['updatePet'](body=dict(id=1, name='Tom1'))
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')

    def test_reuse_req_and_resp(self):
        """ make sure reusing (req, resp) should be fine """
        global pet_db
        cache = sapp.op['updatePet'](body=dict(id=1, name='Tom1'))
        resp = self.client.request(cache)
        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')
        resp = self.client.request(cache)
        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(1)['name'], 'Tom1')

    def test_addPet(self):
        """ addPet """
        global pet_db

        resp = self.client.request(
            sapp.op['addPet'](body=dict(id=5, name='Mission')),
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(5)['name'], 'Mission')

    def test_deletePet(self):
        """ deletePet """
        resp = self.client.request(
            sapp.op['deletePet'](petId=5),
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(pet_db.read_(5), None)

    def test_getPetById(self):
        """ getPetById """
        resp = self.client.request(
            sapp.op['getPetById'](petId=2),
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.data, pet_Mary)

    def test_uploadFile(self):
        """ uploadFile """
        global received_file
        global received_meta

        resp = self.client.request(
            sapp.op['uploadFile'](
                additionalMetadata='a test file', file=dict(data=six.BytesIO(six.b('a test Content')), filename='test.txt')),
        )

        self.assertEqual(resp.status, 200)
        self.assertEqual(received_file.decode(), 'a test Content')
        self.assertEqual(received_meta, 'a test file')

    def test_upload_multiple_files(self):
        """ upload multiple files """
        global received_files
        global received_file_names

        app = App._create_(get_test_data_folder(version='2.0', which=os.path.join('io', 'files')))

        self.client.request(
            app.op['upload_images'](images=[
                dict(data=six.BytesIO(six.b('test image 1')), filename='_1.k'),
                dict(data=six.BytesIO(six.b('test image 2')), filename='_2.k'),
                dict(data=six.BytesIO(six.b('test image 3')), filename='_3.k')
            ])
        )

        # filename
        self.assertEqual(received_files[0].filename, '_1.k')
        self.assertEqual(received_files[1].filename, '_2.k')
        self.assertEqual(received_files[2].filename, '_3.k')

        # parameter name
        self.assertEqual(received_files[0].name, 'images')
        self.assertEqual(received_files[1].name, 'images')
        self.assertEqual(received_files[2].name, 'images')

    def test_custom_headers(self):
        """ test customized headers """
        global received_headers

        headers = {'X-TEST-HEADER': 'aaa'}
        resp = self.client.request(
            sapp.op['updatePet'](body=dict(id=1, name='Tom1')),
            headers=headers
        )

        self.assertEqual(received_headers.get('X-TEST-HEADER'), 'aaa')

    def test_custom_headers_multiple_values_to_one_key(self):
        """ test customized headers with multiple values to one key """

        global received_headers

        headers = [('X-TEST-HEADER', 'aaa'), ('X-TEST-HEADER', 'bbb')]
        resp = self.client.request(
            sapp.op['updatePet'](body=dict(id=1, name='Tom1')),
            headers=headers
        )
        self.assertEqual(received_headers.get_all('X-TEST-HEADER'), ['bbb'])

        # with 'join_headers'
        resp = self.client.request(
            sapp.op['updatePet'](body=dict(id=1, name='Tom1')),
            headers=headers,
            opt={'join_headers': True}
        )
        self.assertEqual(received_headers.get_all('X-TEST-HEADER'), ['aaa,bbb'])


