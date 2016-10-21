import json

from StringIO import StringIO

from prov.model import PROV_REC_CLS, Namespace

from prov.constants import PROV_RECORD_IDS_MAP

from provneo4j.connectors.connector import *
from provneo4j.connectors.deserializer import Deserializer
from provneo4j.connectors.neo4j_rest.neo4j import DOC_PROPERTY_MAP, DOC_PROPERTY_NAME_PROPERTIES_TYPES, \
    DOC_RELATION_TYPE, DOC_PROPERTY_NAME_LABEL, DOC_PROPERTY_NAME_NAMESPACE_URI, DOC_PROPERTY_NAME_NAMESPACE_PREFIX


class Neo4JRestDeserializer(Deserializer):
    def get_properties_without_meta_data(self, properties):
        real_property_keys = set(properties.keys()) - set(DOC_PROPERTY_MAP)
        return filter(lambda (key, value): key in real_property_keys, properties.iteritems())

    def get_properties_as_typed_map(self, properties, type_dic):

        properties = dict(properties)
        for key, value in properties.iteritems():
            if key in type_dic:
                type = type_dic.get(key)
                type.update({
                    "$": value
                })
                properties.update({key: type})
        return properties

    def create_record(self, bundle, db_record):
        jc = []
        # Get type from label
        rec_type = None

        for label in iter(db_record.labels):
            label = Deserializer.valid_qualified_name(bundle, label._label)
            if label in PROV_REC_CLS:
                rec_type = label

        if rec_type is None:
            raise InvalidDataException("A node must provide the type of the node(%s) as label" % db_record.url)

        # Remove all metda-data from the properties

        io = StringIO(db_record.properties.get(DOC_PROPERTY_NAME_PROPERTIES_TYPES))
        types = json.load(io)
        properties = self.get_properties_without_meta_data(db_record.properties)
        properties = self.get_properties_as_typed_map(properties, types)
        # Get id for the node from the properties
        rec_id = db_record.properties.get(DOC_PROPERTY_NAME_LABEL)
        if "Unknown" in rec_id:
            return None
        return Deserializer.create_prov_record(bundle, rec_type, rec_id, properties)

    def create_bundle(self, document, db_record):
        label = db_record.properties.get(DOC_PROPERTY_NAME_LABEL)
        return document.bundle(label)

    def create_relation(self, bundle, db_relation):

        db_relation_type = db_relation.properties.get(DOC_RELATION_TYPE)

        if db_relation_type is None:
            raise ProvSerializerException("Relation must provide the  %s property" % DOC_RELATION_TYPE)

        rec_type = PROV_RECORD_IDS_MAP[db_relation_type]
        if rec_type is None:
            raise InvalidDataException("No valid relation type provided the type was %s" % db_relation.type)

        rec_id = None

        if PROV_RECORD_IDS_MAP[db_relation_type] is None:
            # if custom relation type
            rec_id = Deserializer.valid_qualified_name(bundle, db_relation.type)

        io = StringIO(db_relation.properties.get(DOC_PROPERTY_NAME_PROPERTIES_TYPES))
        types = json.load(io)
        properties = self.get_properties_without_meta_data(db_relation.properties)
        properties = self.get_properties_as_typed_map(properties, types)
        return Deserializer.create_prov_record(bundle, rec_type, rec_id, properties)

    def add_namespace(self, db_node, prov_bundle):
        try:
            prefixes = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_PREFIX]
            uris = db_node.properties[DOC_PROPERTY_NAME_NAMESPACE_URI]
        except KeyError:
            return

        for prefix, uri in zip(prefixes, uris):
            if prefix is not None and uri is not None:
                if prefix != 'default':
                    prov_bundle.add_namespace(Namespace(prefix, uri))
                else:
                    prov_bundle.set_default_namespace(uri)
            else:
                ProvDeserializerException("No valid namespace provided for the node: %s" % db_node)
