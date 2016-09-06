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
        self.base_url = base_url
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
        self._connector.get_document(document_id,prov_format)


    def get_document_meta(self, document_id):
        raise NotImplementedException()


    def post_document(self, prov_document, prov_format, name, public=False):

        if prov_format == "json":
             prov_document = ProvDocument.deserialize(content=prov_document)
        else:
            raise Exception("Not supported format ")

        doc_id = self._connector.post_document(prov_document,name)

        for bundle in prov_document.bundles:
            print self._connector.add_bundle(doc_id,bundle,bundle.identifier)

        return doc_id



    def add_bundle(self, document_id, prov_bundle, identifier):

        prov_document = ProvDocument.deserialize(content=prov_bundle)
        return self._connector.add_bundle(document_id,prov_document, identifier)

    def get_bundles(self, document_id):

        raise NotImplementedException()

    def get_bundle(self, document_id, bundle_id, prov_format=ProvDocument):

        raise NotImplementedException()

    def delete_document(self, document_id):
        return self._connector.delete_doc(document_id)
