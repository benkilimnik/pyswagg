from pyswagr import App, utils
from pyswagr.spec.v2_0 import objects
from ..utils import get_test_data_folder
from ...utils import final
import unittest
import os


class ResolvePathItemTestCase(unittest.TestCase):
    """ test for PathItem $ref """

    @classmethod
    def setUpClass(kls):
        kls.app = App._create_(get_test_data_folder(
            version='2.0',
            which=os.path.join('resolve', 'path_item')
        ))

    def test_path_item(self):
        """ make sure PathItem is correctly merged """
        a = self.app.resolve(utils.jp_compose('/a', '#/paths'))

        self.assertTrue(isinstance(a, objects.PathItem))
        self.assertTrue(a.get.operationId, 'a.get')
        self.assertTrue(a.put.description, 'c.put')
        self.assertTrue(a.post.description, 'd.post')

        b = self.app.resolve(utils.jp_compose('/b', '#/paths'))
        self.assertTrue(b.get.operationId, 'b.get')
        self.assertTrue(b.put.description, 'c.put')
        self.assertTrue(b.post.description, 'd.post')

        c = self.app.resolve(utils.jp_compose('/c', '#/paths'))
        self.assertTrue(b.put.description, 'c.put')
        self.assertTrue(b.post.description, 'd.post')


class ResolveTestCase(unittest.TestCase):
    """ test for $ref other than PathItem """

    @classmethod
    def setUpClass(kls):
        kls.app = App._create_(get_test_data_folder(
            version='2.0',
            which=os.path.join('resolve', 'other')
        ))

    def test_schema(self):
        """ make sure $ref to Schema works """
        p = self.app.s('/a').get

        self.assertEqual(id(p.parameters[2].schema.ref_obj), id(self.app.resolve('#/definitions/d1')))

    def test_parameter(self):
        """ make sure $ref to Parameter works """
        p = self.app.s('/a').get

        self.assertEqual(len(p.parameters), 5)
        self.assertEqual(final(p.parameters[0]).name, 'p1_d')
        self.assertEqual(final(p.parameters[1]).name, 'p2_d')
        self.assertEqual(final(p.parameters[2]).name, 'p2')
        self.assertEqual(final(p.parameters[3]).name, 'p3_d')
        self.assertEqual(final(p.parameters[4]).name, 'p4_d')

    def test_response(self):
        """ make sure $ref to Response works """
        p = self.app.s('/a').get

        self.assertEqual(final(p.responses['default']).description, 'void, r1')

    def test_raises(self):
        """ make sure to raise for invalid input """
        self.assertRaises(ValueError, self.app.resolve, None)
        self.assertRaises(ValueError, self.app.resolve, '')


class DerefTestCase(unittest.TestCase):
    """ test for pyswagr.utils.deref """

    @classmethod
    def setUpClass(kls):
        kls.app = App._create_(get_test_data_folder(
            version='2.0',
            which=os.path.join('resolve', 'deref')
        ))

    def test_deref(self):
        od = utils.deref(self.app.resolve('#/definitions/s1'))

        self.assertEqual(id(od), id(self.app.resolve('#/definitions/s4')))

