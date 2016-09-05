import os
import json
from prov.model import ProvDocument
from provstore.document import Document
from provstore.connectors import  *

class Api(object):
    """
    Main Neo4J-Prov API client object

    Most functions are not used directly but are instead accessed by functions of the Document, BundleManager and Bundle
    objects.

    To create a new Api object:
      >>> from provstore.api import Api
      >>> api = Api(username="provstore username", api_key="api key")

    .. note::
       The username and api_key parameters can also be omitted in which case the client will look for
       **NEO4J_USERNAME** and **NEO4J_API_KEY** environment variables.

    """

    def __init__(self,
                 username=None,
                 api_key=None,
                 base_url=None):
        self._connector = Neo4J()
        self._connector.connect(base_url=base_url, username=username, user_password=api_key)

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
        raise NotImplementedException()


    def get_document_meta(self, document_id):
        raise NotImplementedException()


    def post_document(self, prov_document, prov_format, name, public=False):

        if prov_format == "json":
             prov_document = ProvDocument.deserialize(content=prov_document)
        else:
            raise Exception("Not supported format ")

        return self._connector.post_document(prov_document,name)



    def add_bundle(self, document_id, prov_bundle, identifier):

        raise NotImplementedException()


    def get_bundles(self, document_id):

        raise NotImplementedException()

    def get_bundle(self, document_id, bundle_id, prov_format=ProvDocument):

        raise NotImplementedException()

    def delete_document(self, document_id):

        raise NotImplementedException()
        return True
