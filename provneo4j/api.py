from provneo4j.document import Document
from provdbconnector.provDb import ProvDb
from provdbconnector import Neo4jAdapter
from prov.model import ProvDocument


class ConnectorException(Exception):
    pass


class NotFoundException(ConnectorException):
    pass


class RequestTimeoutException(ConnectorException):
    pass


class InvalidCredentialsException(ConnectorException):
    pass


class ForbiddenException(ConnectorException):
    pass


class InvalidDataException(ConnectorException):
    pass


class UnprocessableException(ConnectorException):
    pass


class DocumentInvalidException(ConnectorException):
    pass


class NotImplementedException(ConnectorException):
    pass


class ProvDeserializerException(ConnectorException):
    pass


class ProvSerializerException(ConnectorException):
    pass


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
                 host=None,
                 bolt_port=7687):
        self.host = host
        self.auth_info = {"user_name": username,
                     "user_password": password,
                     "host": host + ":" + bolt_port
                     }
        self._connector = ProvDb(adapter=Neo4jAdapter,auth_info=self.auth_info)
        self._username = username

    def __eq__(self, other):
        if not isinstance(other, Api):
            return False

        return self.auth_info == other.auth_info

    def __ne__(self, other):
        return not self == other

    @property
    def document(self):
        return Document(self)

    def get_document_prov(self, document_id, prov_format=ProvDocument):

        if prov_format is ProvDocument:
            return self._connector.get_document_as_prov(document_id)
        elif prov_format is "json":
            return self._connector.get_document_as_json(document_id)

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
            return self._connector.create_document_from_json(prov_document)
        else:
            raise Exception("Not supported format ")

    def add_bundle(self, document_id, prov_bundle, identifier):

        #prov_document = ProvDocument.deserialize(content=prov_bundle)
        #return self._connector.add_bundle(document_id, prov_document, identifier)
        pass

    def get_bundles(self, document_id):

        #return self._connector.get_bundles(document_id)
        pass

    def get_bundle(self, document_id, bundle_id, prov_format=ProvDocument):

        #return self._connector.get_document(bundle_id, prov_format)
        pass

    def delete_document(self, document_id):
        #return self._connector.delete_doc(document_id)
        pass
