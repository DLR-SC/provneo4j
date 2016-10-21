from StringIO import StringIO
import json

from prov.constants import *

from neo4j import *
from provneo4j.connectors.connector import *
from provneo4j.connectors.serializer import Serializer


class Neo4jRestSerializer(Serializer):
    def __init__(self, connection):
        Serializer.__init__(self)

        if connection is None:
            raise ProvSerializerException("Neo4j rest Serializer need a connection object ")
        self._connection = connection

    def create_node(self, node):
        # node is a MulitDiGrpah.Node / ProvRecord
        # see: http://networkx.readthedocs.io/en/networkx-1.10/reference/classes.multidigraph.html

        n = self._connection.nodes.create()

        if isinstance(node, ProvElement):
            n.labels.add(str(node.get_type()))
            n.properties = dict(map(lambda (key, value): (Serializer.encode_string_value(key),
                                                          Serializer.encode_string_value(value)),
                                    node.attributes))
        else:
            raise InvalidDataException("Not supported node class you passed %s " % type(node))

        n.set(DOC_PROPERTY_NAME_LABEL, (str(node.identifier)))
        return n

    def create_relation(self, db_from_node, db_to_node, relation):
        # Attributes to string map
        attributes = map(lambda (key, value): (Serializer.encode_string_value(key),
                                               Serializer.encode_string_value(value)), relation.attributes)
        relation_type = PROV_N_MAP[relation.get_type()]

        if relation.label is not None:
            relation_name = str(relation.label)
        elif relation.identifier is not None:
            relation_name = str(relation.identifier)
        elif relation_type is not None:
            relation_name = relation_type
        else:
            raise InvalidDataException(
                "Relation is not valid. The type of the relation is not a default prov relation and has no identifier")

        attributes.append((DOC_RELATION_TYPE, relation_type))

        return db_from_node.relationships.create(relation_name, db_to_node, **dict(attributes))

    def create_bundle_node(self, bundle, identifier):
        n = self._connection.nodes.create()
        n.labels.add(BUNDLE_LABEL_NAME)
        n.set(DOC_PROPERTY_NAME_LABEL, (str(identifier)))
        return n

    def create_bundle_relation(self, db_from_node, db_to_bundle):
        return db_from_node.relationships.create(BUNDLE_RELATION_NAME, db_to_bundle)

    def add_propety_map(self, db_node, prov_record):
        if type(prov_record.attributes) is not None:
            types = {}
            for key, value in prov_record.attributes:
                if key not in PROV_ATTRIBUTES:
                    type_dic = Serializer.encode_json_representation(value)
                    if type_dic is not None:
                        types.update({str(key): type_dic})

            io = StringIO()
            json.dump(types, io)
            io.getvalue()

            db_node.set(DOC_PROPERTY_NAME_PROPERTIES_TYPES, io.getvalue())
        else:
            raise ProvSerializerException("Please provide a prov_record with attributes")

    def add_namespaces(self, db_node, prov_record):
        used_namespaces = {}

        if isinstance(prov_record, QualifiedName):
            # if bundle
            namespace = prov_record.namespace
            used_namespaces.update({str(namespace.prefix): namespace.uri})
        elif isinstance(prov_record.identifier, QualifiedName):
            namespace = prov_record.identifier.namespace
            used_namespaces.update({str(namespace.prefix): namespace.uri})
        elif isinstance(prov_record.label, QualifiedName):
            # if it is a relation instead of a node
            namespace = prov_record.identifier.namespace
            used_namespaces.update({str(namespace.prefix): namespace.uri})
        else:
            logger.info("Prov record %s has no identifier" % prov_record)

        if hasattr(prov_record, 'attributes'):

            for key, value in prov_record.attributes:
                if isinstance(key, QualifiedName):
                    namespace = key.namespace
                    used_namespaces.update({str(namespace.prefix): str(namespace.uri)})
                else:
                    raise ProvSerializerException("Not support key type %s" % type(key))

                if isinstance(value, QualifiedName):
                    namespace = value.namespace
                    used_namespaces.update({str(namespace.prefix): str(namespace.uri)})
                else:
                    qualified_name = Serializer.valid_qualified_name(prov_record.bundle, value)
                    if qualified_name is not None:
                        namespace = qualified_name.namespace
                        used_namespaces.update({str(namespace.prefix): str(namespace.uri)})

        if len(used_namespaces) == 0:
            namespace = PROV
            used_namespaces.update({str(namespace.prefix): str(namespace.uri)})
        db_node.set(DOC_PROPERTY_NAME_NAMESPACE_URI, used_namespaces.values())
        db_node.set(DOC_PROPERTY_NAME_NAMESPACE_PREFIX, used_namespaces.keys())

    def add_bundle_id(self, db_node, doc_id, parent_id):
        db_node.set(DOC_PROPERTY_NAME_ID, parent_id)
        db_node.set(DOC_PROPERTY_BUNDLE_ID, doc_id)

    def add_id(self, db_node, doc_id):
        db_node.set(DOC_PROPERTY_NAME_ID, doc_id)
