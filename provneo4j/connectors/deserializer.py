import logging

from prov.model import parse_xsd_datetime, Literal, \
    Identifier
from prov.constants import PROV_ATTRIBUTES_ID_MAP, PROV_ATTRIBUTES, PROV_MEMBERSHIP, \
    PROV_ATTR_ENTITY, PROV_ATTRIBUTE_QNAMES, PROV_ATTR_COLLECTION, XSD_ANYURI, PROV_QUALIFIEDNAME

from connector import *

logger = logging.getLogger(__name__)


class Deserializer:
    @staticmethod
    def decode_json_representation(literal, bundle):
        if isinstance(literal, dict):
            # complex type
            value = literal['$']
            datatype = literal['type'] if 'type' in literal else None
            datatype = Deserializer.valid_qualified_name(bundle, datatype)
            langtag = literal['lang'] if 'lang' in literal else None
            if datatype == XSD_ANYURI:
                return Identifier(value)
            elif datatype == PROV_QUALIFIEDNAME:
                return Deserializer.valid_qualified_name(bundle, value)
            else:
                # The literal of standard Python types is not converted here
                # It will be automatically converted when added to a record by
                # _auto_literal_conversion()
                return Literal(value, datatype, langtag)
        else:
            # simple type, just return it
            return literal

    @staticmethod
    def valid_qualified_name(bundle, value):
        if value is None:
            return None
        qualified_name = bundle.valid_qualified_name(value)
        return qualified_name

    @staticmethod
    def create_prov_record(bundle, prov_type, prov_id, properties):
        """

        :param prov_type: valid prov type like prov:Entry as string
        :param prov_id: valid id as string like <namespace>:<name>
        :param properties: dict{attr_name:attr_value} dict with all properties (prov and additional)
        :return: ProvRecord
        """
        # Parse attributes
        if isinstance(properties, dict):
            properties_list = properties.iteritems()
        elif isinstance(properties, list):
            properties_list = properties
        else:
            raise ProvDeserializerException(
                "please provide properties as list[(key,value)] or dict your provided: %s" % properties.__class__.__name__)

        attributes = dict()
        other_attributes = []
        # this is for the multiple-entity membership hack to come
        membership_extra_members = None
        for attr_name, values in properties_list:

            attr = (
                PROV_ATTRIBUTES_ID_MAP[attr_name]
                if attr_name in PROV_ATTRIBUTES_ID_MAP
                else Deserializer.valid_qualified_name(bundle, attr_name)
            )
            if attr in PROV_ATTRIBUTES:
                if isinstance(values, list):
                    # only one value is allowed
                    if len(values) > 1:
                        # unless it is the membership hack
                        if prov_type == PROV_MEMBERSHIP and \
                                        attr == PROV_ATTR_ENTITY:
                            # This is a membership relation with
                            # multiple entities
                            # HACK: create multiple membership
                            # relations, one x each entity

                            # Store all the extra entities
                            membership_extra_members = values[1:]
                            # Create the first membership relation as
                            # normal for the first entity
                            value = values[0]
                        else:
                            error_msg = (
                                'The prov package does not support PROV'
                                ' attributes having multiple values.'
                            )
                            logger.error(error_msg)
                            raise ProvDeserializerException(error_msg)
                    else:
                        value = values[0]
                else:
                    value = values
                value = (
                    Deserializer.valid_qualified_name(bundle, value)
                    if attr in PROV_ATTRIBUTE_QNAMES
                    else parse_xsd_datetime(value)
                )
                attributes[attr] = value
            else:
                if isinstance(values, list):
                    other_attributes.extend(
                        (
                            attr,
                            Deserializer.decode_json_representation(value, bundle)
                        )
                        for value in values
                    )
                else:
                    # single value
                    other_attributes.append(
                        (
                            attr,
                            Deserializer.decode_json_representation(values, bundle)
                        )
                    )
        record = bundle.new_record(
            prov_type, prov_id, attributes, other_attributes
        )
        # HACK: creating extra (unidentified) membership relations
        if membership_extra_members:
            collection = attributes[PROV_ATTR_COLLECTION]
            for member in membership_extra_members:
                bundle.membership(
                    collection, Deserializer.valid_qualified_name(bundle, member)
                )
        return record
