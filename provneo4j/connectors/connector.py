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


class Connector:
    """
        Neo4j Connector model.

        .. note::
            This clas is an abstract class
    """

    def connect(self):
        """
             Create the connection and authenticate the user
        """
        raise NotImplementedError("Please implement the method 'connect' in your connector class")

    def get_document(self, document_id, prov_format=ProvDocument):
        """
        Get the document from the database
        :param document_id: <int> the id of the document
        :param prov_format: <model.ProvDocument> per default
        :return: :py:class:`prov.model.ProvDocument`
        """
        raise NotImplementedError("Please implement the method 'get_document' in your connector class")

    def get_bundle(self, bundle_id, prov_format=ProvDocument, parent_prov_document=None, bundle_identifier=None):
        """
        Get a bundle
        :param bundle_id: <int> The bundle id
        :param prov_format: :py:class:`prov.model.ProvDocument` per default the prov document
        :param parent_prov_document: :py:class:`prov.model.ProvDocument` the parent prov document
        :param bundle_identifier: <str|QualifiedName> The identifier for the bundle, must be unique in the document.

        :return: :py:class:`prov.model.ProvDocument`
        """
        raise NotImplementedError("Please implement the method 'get_bundle' in your connector class")

    def get_bundles(self, document_id):
        """
        Get a list of the containing bundles
        :param document_id: <int> the id of the document
        :return: <List()> A list of bundles with meta information

        .. note::
            The return object contains the following properties:

            >>> {
            >>>     "id": 0,
            >>>     "created_at": "xds:datetime"
            >>>     "identifier": "label of the bundle"
            >>> }


        """
    def post_document(self, prov_document, name=None):
        """
        Saved the document into the database
        :param prov_document: :py:class:`prov.model.ProvDocument`
        :param name: <str> the identifier for the document
        :return: <int> the id of the generated document
        """
        raise NotImplementedError("Please implement the method 'post_document' in your connector class")

    def add_bundle(self, document_id, bundle_document, identifier):
        """

        :param document_id: <int> the id of the document
        :param bundle_document: :py:class:`prov.model.ProvBundle` the bundle that should be stored
        :param identifier: :py:class:`prov.model.QualifiedName` An individual, unique sting
        :return: :py:class:`prov.model.ProvDocument`
        """

        raise NotImplementedError("Please implement the method 'post_document' in your connector class")

    def delete_document(self, document_id):
        """

        :param document_id: <int>
        :return:<bool>
        """
        raise NotImplementedError("Please implement the method 'post_document' in your connector class")
