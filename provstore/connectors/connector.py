import abc
from prov.graph import prov_to_graph

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

    def connect(self):
        raise NotImplementedError("Please implement the method 'connect' in your connector class")

    def post_document(self,prov_document,name=None):
        # creates a database entry from a prov-n document
        # returns the saved neo4J doc
        #

        # create graph from prov doc
        g = prov_to_graph(prov_document)

        # store all database nodes in dict
        db_nodes = {}

        # Create nodes
        for node in g.nodes():
            db_nodes[node] = self._create_db_node(node)


        # Create relations
        for from_node, to_node, relations in g.edges_iter(data=True):

            # interate over relations (usually only one item)
            for key, relation in relations.iteritems():
                self._create_relation(db_nodes, from_node, to_node, relation)

        return None

