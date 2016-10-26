from provneo4j.document import Document
from provneo4j.connectors.neo4j_rest.neo4j import Neo4J
from provneo4j.connectors.connector import *


class Api(object):
    """
    Main Neo4J PROV API client object

    Most functions are not used directly but are instead accessed by functions of the Document, BundleManager and Bundle
    objects.

    To create a new Api object:
      >>> from provneo4j.api import Api
      >>> api = Api(username="your_neo4j_username" password="your_neo4j_password")

    .. note::
       The username and api_key parameters can also be omitted in which case the client will look for
       **NEO4J_USERNAME** and **NEO4J_PASSWORD** environment variables.

    """

    def __init__(self,
                 username=None,
                 password=None,
                 base_url=None):
        self.base_url = base_url
        self._connector = Neo4J()
        self._connector.connect(base_url=base_url, username=username, user_password=password)
        self._username = username

    def __eq__(self, other):
        if not isinstance(other, Api):
            return False

        return self.base_url == other.base_url

    def __ne__(self, other):
        return not self == other

    @property
    def document(self):
        return Document(self)

    def get_document_prov(self, document_id, prov_format=ProvDocument):
        return self._connector.get_document(document_id, prov_format)

    def get_document_meta(self, document_id):
        metadata = {}
        metadata['document_name'] = "Not supported"
        metadata['public'] = True
        metadata['owner'] = "Not supported"
        metadata['created_at'] = "01.01.2016 12:00:00"
        metadata['views_count'] = 0
        return metadata

    def post_document(self, prov_document, prov_format, name, public=False):

        if prov_format == "json":
            prov_document = ProvDocument.deserialize(content=prov_document)
        else:
            raise Exception("Not supported format ")

        return self._connector.post_document(prov_document, name)

    def add_bundle(self, document_id, prov_bundle, identifier):

        prov_document = ProvDocument.deserialize(content=prov_bundle)
        return self._connector.add_bundle(document_id, prov_document, identifier)

    def get_bundles(self, document_id):

        return self._connector.get_bundles(document_id)

    def get_bundle(self, document_id, bundle_id, prov_format=ProvDocument):

        return self._connector.get_document(bundle_id, prov_format)

    def delete_document(self, document_id):
        return self._connector.delete_doc(document_id)
