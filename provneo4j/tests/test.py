import os
import unittest
import datetime
from time import gmtime,strftime
from provneo4j.api import Api, NotFoundException, InvalidCredentialsException, InvalidDataException, ForbiddenException
from provneo4j.document import AbstractDocumentException, ImmutableDocumentException, EmptyDocumentException
import provneo4j.tests.examples as own_examples
from prov.tests import examples

NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'neo4jneo4j') #Password
NEO4J_BASE_URL =  os.environ.get('NEO4J_BASE_URL', 'http://localhost:7474/db/data/')

class LoggedInAPITestMixin(object):
    @classmethod
    def setUpClass(cls):
        cls.api = Api(base_url=NEO4J_BASE_URL,username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        return super(LoggedInAPITestMixin, cls).setUpClass()


class ProvStoreAPITests(LoggedInAPITestMixin, unittest.TestCase):
    def test_basic_storage(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        self.assertEqual(stored_document.prov, prov_document)

        stored_document.delete()

    def test_basic_get(self):
        prov_document = own_examples.flat_document()
        prov_document.entity("ex:string", other_attributes={"ex:name":"test"})
        prov_document.entity("ex:date",other_attributes={"ex:date":strftime("%Y%m%dT%H%M%S%Z", gmtime())})
        prov_document.wasAssociatedWith('ex:string', 'ex:date')
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()


    def test_prov_primer_example(self):
        prov_document = examples.primer_example()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")


        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()
    @unittest.skip("Not supported on travis-cli")
    def test_prov__primer_example_alternate(self):
        prov_document = examples.primer_example_alternate()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")


        query_document = stored_document.refresh()

        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    def test_prov_w3c_publication_1(self):
        prov_document = examples.w3c_publication_1()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    def test_prov_w3c_publication_2(self):
        prov_document = examples.w3c_publication_2()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    def test_prov_bundles1(self):
        prov_document = examples.bundles1()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    def test_prov_bundles2(self):
        prov_document = examples.bundles2()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()
    def test_prov_datatypes(self):
        prov_document = examples.datatypes()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    def test_prov_long_literals(self):
        prov_document = examples.long_literals()
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        query_document = stored_document.refresh()
        self.assertEqual(query_document.prov, prov_document)

        stored_document.delete()

    @unittest.skip("Not supported with neo4J")
    def test_diff_auth_access(self):
        prov_document = own_examples.flat_document()

        # Private
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage")

        public_api = Api()

        with self.assertRaises(ForbiddenException):
            public_api.document.get(stored_document.id)

        # Public
        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_storage",
                                                   public=True)
        document = public_api.document.get(stored_document.id)
        self.assertEqual(document.id, stored_document.id)

    def test_basic_bundle_storage(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_basic_bundle_storage")

        stored_document.add_bundle(prov_document, identifier="ex:bundle-1")
        stored_document.bundles['ex:bundle-2'] = prov_document

        # should be a match even though we've added a bundle, this is a stale
        # instance
        self.assertEqual(stored_document.prov, prov_document)

        # when we refresh it, it should no longer match
        self.assertNotEqual(stored_document.refresh().prov, prov_document)

        self.assertEqual(stored_document.bundles['ex:bundle-2'].prov, prov_document)

        #self.assertEqual(self.api.document.read_meta(stored_document.id).name, "test_basic_bundle_storage")

        self.assertTrue(isinstance(stored_document.bundles['ex:bundle-2'].created_at, datetime.datetime))

        stored_document.delete()

    def test_bundle_iteration(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_bundle_iteration")

        stored_document.add_bundle(prov_document, identifier="ex:bundle-1")
        stored_document.bundles['ex:bundle-2'] = prov_document

        self.assertEqual(len(stored_document.bundles), 0)
        self.assertEqual({u'ex:bundle-1', u'ex:bundle-2'},
                         set([bundle.identifier for bundle in stored_document.bundles]))
        self.assertEqual(len(stored_document.bundles.refresh()), 2)

        stored_document.delete()

    def test_basic_bundle_retrieval(self):
        prov_document = own_examples.flat_document()

        stored_document1 = self.api.document.create(prov_document,
                                                    name="test_basic_bundle_retrieval")

        stored_document2 = self.api.document.create(prov_document,
                                                    name="test_basic_bundle_retrieval")

        retrieved_document = self.api.document.set(stored_document1.id)

        self.assertEqual(stored_document1, retrieved_document)
        self.assertNotEqual(stored_document2, retrieved_document)

        stored_document1.delete()
        stored_document2.delete()

    def test_non_existent_bundle(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_non_existent_bundle")

        with self.assertRaises(NotFoundException):
            stored_document.bundles['ex:not-there']

        stored_document.delete()

    def test_non_existent_document(self):
        with self.assertRaises(NotFoundException):
            self.api.document.get(-1)

    def test_lazy_instantiation_of_props(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_lazy_instantiation_of_props")

        self.assertEqual(self.api.document.set(stored_document.id).views, 0)
        #self.assertEqual(self.api.document.set(stored_document.id).owner, self.api._username)
        self.assertTrue(isinstance(self.api.document.set(stored_document.id).created_at, datetime.datetime))
        self.assertEqual(self.api.document.set(stored_document.id).prov, prov_document)
        self.assertTrue(self.api.document.set(stored_document.id).public)
        #self.assertEqual(self.api.document.set(stored_document.id).name, "test_lazy_instantiation_of_props")

        stored_document.delete()

    def test_document_props(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document,
                                                   name="test_document_props")

        self.assertEqual(stored_document.views, 0)
        #self.assertEqual(stored_document.owner, self.api._username)
        self.assertTrue(isinstance(stored_document.created_at, datetime.datetime))
        self.assertEqual(stored_document.prov, prov_document)
        self.assertTrue(stored_document.public)
        #self.assertEqual(stored_document.name, "test_document_props")

        stored_document.delete()

    def test_empty_exceptions(self):
        with self.assertRaises(EmptyDocumentException):
            self.api.document.views
        with self.assertRaises(EmptyDocumentException):
            self.api.document.created_at
        with self.assertRaises(EmptyDocumentException):
            self.api.document.owner
        with self.assertRaises(EmptyDocumentException):
            self.api.document.prov
        with self.assertRaises(EmptyDocumentException):
            self.api.document.public
        with self.assertRaises(EmptyDocumentException):
            self.api.document.name

    def test_abstract_exceptions(self):
        prov_document = own_examples.flat_document()

        abstract_document = self.api.document

        with self.assertRaises(AbstractDocumentException):
            abstract_document.bundles
        self.assertRaises(AbstractDocumentException, abstract_document.delete)
        with self.assertRaises(AbstractDocumentException):
            abstract_document.add_bundle(prov_document, 'ex:bundle')
        self.assertRaises(AbstractDocumentException, abstract_document.read_meta)
        self.assertRaises(AbstractDocumentException, abstract_document.read_prov)

    def test_immutable_exceptions(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document, name="test_immutable_exceptions")

        self.assertRaises(ImmutableDocumentException, stored_document.create, (stored_document,))
        self.assertRaises(ImmutableDocumentException, stored_document.set, (1,))
        self.assertRaises(ImmutableDocumentException, stored_document.get, (1,))
        self.assertRaises(ImmutableDocumentException, stored_document.read_prov, (1,))
        self.assertRaises(ImmutableDocumentException, stored_document.read_meta, (1,))
        self.assertRaises(ImmutableDocumentException, stored_document.read, (1,))

        stored_document.delete()

    def test_equality(self):
        prov_document = own_examples.flat_document()

        stored_document = self.api.document.create(prov_document, name="test_equality")

        self.assertFalse(stored_document == "document")

        stored_document.delete()

    def test_invalid_name(self):
        prov_document = own_examples.flat_document()

        with self.assertRaises(InvalidDataException):
            self.api.document.create(prov_document, name="")


class ProvStoreConfigAPITests(unittest.TestCase):
    def test_invalid_credentials(self):
        with self.assertRaises(InvalidCredentialsException):
            api = Api(username="millar", password="bad")
            api.document.get(148)

    @unittest.skip("Not supported with neo4J")
    #https://github.com/travis-ci/travis-ci/issues/3243
    def test_public_access(self):
        api = Api()
        stored_document = api.document.get(148)
        self.assertEqual(stored_document.id, 148)