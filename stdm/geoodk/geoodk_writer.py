"""
/***************************************************************************
Name                 : GeoODK Writer class write Xform sections into the XFORMDocument creator class
Description          : XFORMDocument provides the form and the writer will
                        write all the data in the form.
Date                 : 30/May/2017
copyright            : (C) 2017 by UN-Habitat and implementing partners.
                       See the accompanying file CONTRIBUTORS.txt in the root
email                : stdm@unhabitat.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from qgis.PyQt.QtCore import (
    QFile,
    QIODevice,
    QDate,
    QFileInfo,
    QDir
)
from qgis.PyQt.QtXml import (
    QDomDocument,
    QDomElement,
    QDomText
)

from stdm.data.configfile_paths import FilePaths
from stdm.geoodk.geoodk_reader import (
    GeoODKReader
)
from stdm.geoodk.xform_model import EntityFormatter
from stdm.ui.forms.widgets import BooleanColumn

from stdm.settings import current_profile

DOCSUFFIX = 'h'
DOCEXTENSION = '.xml'
XFOFMDEFAULTS = ['start', 'end', 'deviceid', 'today']
BINDPARAMS = "jr:preloadParams"
CUSTOMBINDPARAMS = "jr:preload"
DOCUMENT = 'supporting_document'

HOME = QDir.home().path()

FORM_HOME = HOME + '/.stdm/geoodk/forms'


class XFORMDocument:
    """
    class to generate an Xml file that is needed for data collection
    using mobile device. The class creates the file and QDOM sections
    for holding data once the file is called
    """
    def __init__(self, file_name: str):
        """
        Initalize the class so that we have a new file
        everytime document generation method is called.
        `file_name` is a string representing the current profile name.
        """
        self.dt_text = QDate()
        self.file_handler = FilePaths()
        self.doc = QDomDocument()
        self.form = None
        self.file_name = file_name+DOCEXTENSION
        self.doc_with_entities = []
        self.supports_doc = self.document()

    def document(self):
        """
        use the globally defined Document name for supporting document
        :return:
        """
        global DOCUMENT
        return DOCUMENT


    def form_name(self):
        """
        Format the name for the new file to be created. We need to ensure it is
        .xml file.
        :return:
        """
        if len(self.file_name.split(".")) > 1:
            return self.file_name
        else:
            return self.file_name + "{}".format(DOCEXTENSION)

    # def set_form_name(self, local_name):
    #     """
    #     Allow the user to update the name of the file. This method
    #     will be called to return a new file with the local_name given
    #     :param local_name: string
    #     :return: QFile
    #     """
    #     self.file_name = local_name + "{}".format(DOCEXTENSION)
    #     self.form.setFileName(self.file_name)
    #     self.create_form()

    #     return self.file_name

    def create_form(self) ->tuple[bool, str]:
        """
        Create's an XML file that will be our XFORM Document for reading and writing.
        """
        self.form = QFile(os.path.join(FORM_HOME, self.file_name))

        # if not QFileInfo(self.form).suffix() == DOCEXTENSION:
        #     self.form_name()

        if not self.form.open(QIODevice.ReadWrite | QIODevice.Truncate |
                              QIODevice.Text):
            error = self.form.error()
            failed = False
            reason = ""

            if error == QFile.OpenError:
                reason  = "The file could not be opened."

            if error == QFile.AbortError:
                reason = "The operation was aborted."

            if error == QFile.TimeOutError:
                reason = "A timeout occurred."

            if error == QFile.UnspecifiedError:
                reason = "An unspecified error occurred."

            self.form = None
            return failed, reason

        return True, ""

    def create_node(self, node_name: str)->QDomElement:
        """
        Create a XML DOM Element
        """
        return self.doc.createElement(node_name)

    def create_text_node(self, text) ->QDomText:
        """
        Create an XML text node
        :param text:
        :return:
        """
        return self.doc.createTextNode(text)

    def create_node_attribute(self, node, key, value):
        """
        Create an attribute and attach it to the node
        :param node: Qnode
        :param key: Qnode name
        :param value: Qnode value
        :return: QNode
        """
        return node.setAttribute(key, value)

    def xform_document(self):
        """
        :return: QDomDocument
        """
        return self.doc

    def write_to_file(self, xml_file: str, dom_doc: QDomDocument) -> int:
        """
        Write data to xml file from the base calling class to an output file created earlier
        """
        written_bytes = xml_file.write(dom_doc.toByteArray())
        xml_file.close()
        dom_doc.clear()

        return written_bytes

    def update_form_data(self):
        """
        Update the xml file with changes that the user has made.
        Particular section of the document will be deleted or added
        :return:
        """
        pass


class GeoodkWriter(EntityFormatter, XFORMDocument):
    """
    Class reads current profile entities and attributes and writes
        the data into an Xml file for mobile data collection
    """

    def __init__(self, entities: list[str], str_supported: bool):
        """
        Class initialization
        :param entities: profile entities
        :param str_supported: bool
        """
        self.entities = entities
        self.entity_read = None
        self.profile_name = current_profile().name.replace(' ', '_')
        self.supports_str = str_supported

        XFORMDocument.__init__(self, self.profile_name)
        EntityFormatter.__init__(self, self.profile_name)


    def create_entity_reader(self, entity: str) -> GeoODKReader:
        """
        Initialize the reader class after each entity to avoid
        redundant data
        """
        self.entity_read = GeoODKReader(entity)
        return self.entity_read

    def create_xml_file(self) -> tuple[bool, str]:
        return self.create_form()

    def _doc_meta_instance(self):
        """
        Create a meta section that will hold the GUUID of the form
        :return:
        """
        meta_node = self.create_node("meta")
        meta_id = self.create_node("instanceID")
        meta_node.appendChild(meta_id)
        return meta_node

    def create_xform_root_node(self):
        """
        Method to read and check the header node in the Xform document
        :return: Dom element
        """
        self.xform_document().appendChild(
            self.xform_document().createProcessingInstruction("xml", "version=\"1.0\" "))
        root = self.create_node("h:html")
        root.setPrefix(DOCSUFFIX)
        root.setAttribute("xmlns", "http://www.w3.org/2002/xforms")
        root.setAttribute("xmlns:ev",
                          "http://www.w3.org/2001/xml-events")
        root.setAttribute("xmlns:h", "http://www.w3.org/1999/xhtml")

        root.setAttribute("xmlns:orx", "http://openrosa.org/xforms")
        root.setAttribute("xmlns:xsd",
                          "http://www.w3.org/2001/XMLSchema")
        root.setAttribute("xmlns:jr", "http://openrosa.org/javarosa")
        return root

    def header_fragment_data(self):
        """
        Create and add data to the header node in Xform document
        :return:
        """
        doc_header = self.create_node("h:head")
        doc_header.setPrefix(DOCSUFFIX)
        doc_header.appendChild(self._header_title())
        doc_header.appendChild(self._header_node())
        return doc_header

    def _header_title(self):
        """
        Create header title in the document that is required by GeoODK
        :return:
        """
        title = self.create_node("h:title")
        title_text = self.create_text_node(current_profile().name)
        title.appendChild(title_text)
        return title

    def _append_nodes(self, parent_node:QDomElement, child_nodes:list[QDomElement]):
        for child_node in child_nodes:
            parent_node.appendChild(child_node)

    def _header_node(self) ->QDomElement:
        """
        Create a header model that GeoODK writer requires to create form
        :return:
        """
        # profile_node = self.create_node(self.profile_name)
        # if self.supports_str:
        #     self.include_social_tenure(profile_node)
        # profile_node.setAttribute("id", self.profile_name.replace('_', ' ').title())
        # entity_nodes = self.create_entity_nodes()
        # self._append_nodes(profile_node, entity_nodes)
        # instance_node = self.create_node("instance")
        # instance_node.appendChild(profile_node)
        # instance_node.appendChild(self._doc_meta_instance())

        model_node = self.create_node("model")
        model_node.appendChild(self._create_model_props())
        # model_node.appendChild(instance_node)

        self.bind_default_parameters(model_node)
        self.create_model_bind_attributes(model_node)
        model_node.appendChild(self.model_unique_id_generator())
        return model_node

    def _create_model_props(self):
        instance = self.create_node("instance")
        return self.on_instance_id_set_columns(instance)

    def initialize_entity_reader(self, entity):
        self.entity_read = GeoODKReader(entity)
        return self.entity_read

    def on_instance_id_set_columns(self, instance):
        """
        Create an instance that will hold entity columns in Xform list
        :param instance: str
        :return:
        """
        instance_id = self.create_node(self.profile_name)
        instance_id.setAttribute("id", self.profile_name.replace('_',' ').title())
        """ add entity data into the instance node as form fields,
        language translation aspect of the instance child 
        has not been considered
        """
        if isinstance(self.entities, list):
            for entity in self.entities:
                self.initialize_entity_reader(entity)
                entity_values = self.entity_read.read_attributes()
                field_group = self.create_node(self.entity_read.default_entity())
                if self.entity_read.on_column_show_in_parent():
                    field_group.setAttribute('jr:template', '')
                entity_group = self.entity_supports_documents(field_group, entity_values)
                instance_id.appendChild(entity_group)

                instance.appendChild(instance_id)
            if self.supports_str:
                self.include_social_tenure(instance_id)
            instance_id.appendChild(self._doc_meta_instance())
            return instance


    def create_entity_nodes(self):
        """
        Create an instance that will hold entity columns in Xform list
        """
        entity_nodes = []

        """ add entity data into the instance node as form fields """
        # TODO: Consider language translation aspect of the child instance
        for entity_name in self.entities:
            reader = self.create_entity_reader(entity_name)
            entity_values = reader.read_attributes()
            entity_node = self.create_node(entity_name.replace(' ','_'))
            if reader.on_column_show_in_parent():
                entity_node.setAttribute('jr:template', '')
            entity_node_with_support_docs = self.entity_supports_documents(entity_node, entity_values)
            entity_nodes.append(entity_node_with_support_docs)

        return entity_nodes


    def entity_supports_documents(self, field_group, entity_values):
        """
        Allow for document capturing in the form if it has been provided for
        in the entity creation.
        :param1: node
        :type: QDom node
        :param2: entity_values
        :type:dict
        :return: node
        """
        self.doc_with_entities = []
        # entity = current_profile().entity(entity_name)
        #if entity.supports_documents:
        if self.entity_read.entity_has_supporting_documents():
            doc_list = self.entity_read.entity_supported_document_types()
            #doc_list = entity.document_types_non_hex()
            ''' we need to create a node for adding documents'''
            self.doc_with_entities.append(self.entity_read.user_entity_name())
            #self.doc_with_entities.append(entity.name)
            for key_field in entity_values.keys():
                col_node = self.create_node(key_field)
                field_group.appendChild(col_node)
            if len(doc_list) < 2:
                document_node = self.create_node(self.supports_doc)
                field_group.appendChild(document_node)
            else:
                for doc in doc_list:
                    if doc == 'General':
                        continue
                    document_node = self.create_node(doc.replace(' ', '-') + '_' + self.supports_doc)
                    field_group.appendChild(document_node)
        else:
            for key_field in entity_values.keys():
                col_node = self.create_node(key_field)
                field_group.appendChild(col_node)

        return field_group

    def _str_columns(self) ->dict[str, str]:
        """
        Get social tenure attributes
        """
        str_columns = {}
        for obj in list(current_profile().social_tenure.columns.values()):
            if str(obj.name).endswith('id'):
                continue
            str_columns[obj.name] = obj.TYPE_INFO
        return str_columns

    def include_social_tenure(self, parent):
        """
        Add social tenure details on the form if the user has
        selected them to be included in the final mobile form
        :param: parent
        :type: String representing the parent Qnode to attach the columns
        :return: QDomnode
        """
        #entity = current_profile().entity(entity_name)
        group_node = self.create_node('social_tenure')
        #str_entities = list(self.entity_read.social_tenure_attributes().keys())
        str_entities = list(self._str_columns().keys())
        if self.check_str_supports_multiple_entities():
            str_entities.append('party')
            str_entities.append('spatial_unit')

        for entity in str_entities:
            entity = self.create_node(entity)
            group_node.appendChild(entity)

        parent.appendChild(group_node)
        #doc_list = self.entity_read.profile().social_tenure.document_types_non_hex()
        doc_list = current_profile().social_tenure.document_types_non_hex()
        if doc_list is not None:
            if len(doc_list) < 2:
                document_node = self.create_node(self.supports_doc)
                group_node.appendChild(document_node)
            else:
                for doc in doc_list:
                    if doc == 'General':
                        continue
                    document_node = self.create_node(doc.replace(' ', '-') + '_' + self.supports_doc)
                    group_node.appendChild(document_node)

            parent.appendChild(group_node)

    def entity_with_supporting_documents(self):
        """
        return a list of entity with supporting documents
        :return: list
        """
        return self.doc_with_entities

    def create_model_bind_attributes(self, base_node):
        """
        We need to iterate through each entity and bind the columns
        to xform format. The order does not matter
        :return:
        """
        if isinstance(self.entities, list):
            for entity in self.entities:
                reader = self.create_entity_reader(entity)
                entity_values = reader.read_attributes()
                self.bind_model_attributes(base_node, entity_values)
            if self.supports_str:
                self.social_tenure_bind_to_node(base_node)

    def bind_model_attributes(self,  base_node, entity_values):
        """
        Method to create bind section of the form.
        Each attribute is bound to XForm property
        Creates XPath link for the attribute field
        Format the attribute data type to the XForm type
        :return:
        """
        if hasattr(entity_values, "id"):
            entity_values.pop("id")
        for key, val in entity_values.items():
            bind_node = self.create_node("bind")
            entity_name = self.entity_read.default_entity()
            bind_node.setAttribute("nodeset",
                                   self.set_model_xpath(key, entity_name))
            if self.entity_read.col_is_mandatory(key):
                bind_node.setAttribute("required", "true()")
            if val == 'GEOMETRY':
                geoshape_type = self.geometry_types(self.entity_read.entity_object(), key)
                bind_node.setAttribute("type", self.geom_selector(geoshape_type))
            else:
                bind_node.setAttribute("type", self.set_model_data_type(val))
            base_node.appendChild(bind_node)

        if self.entity_read.entity_has_supporting_documents():
            self.add_supporting_docs_to_bind_node(base_node)

        return base_node

    def social_tenure_bind_to_node(self, base_node):
        """
        Add social tenure parameters to the bind section
        :param base_node: string
        :return: QDomnode
        """
        str_data = self.entity_read.social_tenure_attributes()
        if self.check_str_supports_multiple_entities():
            str_data['party'] = 'LOOKUP'
            str_data['spatial_unit'] = 'LOOKUP'
        for str_node, str_data_type in str_data.items():
            str_bind_node = self.create_node('bind')
            str_bind_node.setAttribute('nodeset', self.set_model_xpath(str_node,
                                                                       'social_tenure'))
            str_bind_node.setAttribute("type", self.set_model_data_type(str_data_type))
            base_node.appendChild(str_bind_node)

        doc_list = self.entity_read.profile().social_tenure.document_types_non_hex()
        if doc_list is not None:
            if len(doc_list) < 2:
                doc_bind_node = self.create_node("bind")
                doc_bind_node.setAttribute("nodeset",
                                           self.set_model_xpath(self.supports_doc,
                                                                'social_tenure'))
                doc_bind_node.setAttribute("type", 'binary')
                base_node.appendChild(doc_bind_node)
            else:
                for doc in doc_list:
                    if doc == 'General':
                        continue
                    doc_bind_node = self.create_node("bind")
                    doc_bind_node.setAttribute("nodeset",
                                               self.set_model_xpath(doc.replace(' ', '-') + '_' + self.supports_doc,
                                                                    'social_tenure'))
                    doc_bind_node.setAttribute("type", 'binary')
                    base_node.appendChild(doc_bind_node)

    def add_supporting_docs_to_bind_node(self, parent_node):
        """
        Add all supporting document type to bind node so that they are
        available in the form
        :param: parent_node
        :type: string
        :return: node
        :rtype:QDomNode
        """
        doc_list = self.entity_read.entity_supported_document_types()
        if len(doc_list) < 2:
            doc_bind_node = self.create_node("bind")
            doc_bind_node.setAttribute("nodeset",
                                       self.set_model_xpath(self.supports_doc,
                                                            self.entity_read.default_entity()))
            doc_bind_node.setAttribute("type", 'binary')
            parent_node.appendChild(doc_bind_node)
        else:
            for doc in doc_list:
                if doc == 'General':
                    continue
                doc_bind_node = self.create_node("bind")
                doc_bind_node.setAttribute("nodeset",
                                           self.set_model_xpath(doc.replace(' ', '-') + '_' + self.supports_doc,
                                                                self.entity_read.default_entity()))
                doc_bind_node.setAttribute("type", 'binary')
                parent_node.appendChild(doc_bind_node)

        return parent_node

    def model_unique_id_generator(self):
        """
        Create static fields that  needed by XForm to hold instance GUUID
        :return:
        """
        bind_node = self.create_node("bind")
        bind_node.setAttribute("calculate", self.model_unique_uuid())
        bind_node.setAttribute("nodeset", self.set_model_xpath("meta/instanceID"))
        bind_node.setAttribute("readonly", "True")
        bind_node.setAttribute("type", "string")
        return bind_node

    def bind_default_parameters(self, parent_node):
        """
        Ensure that the default parameters for Xform are included
        :return:
        """
        cast_param = ""
        for item_val in XFOFMDEFAULTS:
            bind_node = self.create_node("bind")
            if item_val == "deviceid":
                cast_param = "property"
            else:
                cast_param = "timestamp"
            bind_node.setAttribute(CUSTOMBINDPARAMS, cast_param)
            bind_node.setAttribute(BINDPARAMS, item_val)
            bind_node.setAttribute("nodeset", self.set_model_xpath(item_val))
            bind_node.setAttribute("type", self.xform_custom_params_types(item_val))
            parent_node.appendChild(bind_node)
        return parent_node

    def _body_section(self) -> QDomElement:
        """
        Method to read and populate the body node in the Xform document is created
        :return: Dom element
        """
        body_section_node = self.create_node("h:body")
        self.create_nested_entity_data(body_section_node)
        if self.supports_str:
            self.social_tenure_label(body_section_node)
        return body_section_node

    def create_nested_entity_data(self, parent_node: QDomElement):
        """
        Format each entity into groups so that each holds only one entity information
        """
        if isinstance(self.entities, list):
            for entity in self.entities:
                reader = self.create_entity_reader(entity)
                reader.set_user_selected_entity()
                #self.entity_read.set_user_selected_entity()

                entity_values = reader.read_attributes()
                group_node, repeat_node = self.body_section_categories(
                    reader.default_entity())
                if not repeat_node:
                    self._body_section_data(reader, entity_values, group_node)
                else:
                    self._body_section_data(reader, entity_values, repeat_node)
                parent_node.appendChild(group_node)
            return parent_node

    def body_section_categories(self, entity) ->tuple[QDomElement, QDomElement]:
        """
        Create groups that will contain each entity information
        :param item:
        :return:
        """
        repeat_node = None
        ref = 'ref'

        title = self.entity_read.user_entity_name().replace(' ', '_')
        dom_text = self.create_text_node(title)

        cate_name = self.model_category_group(self.profile_name,
                                              entity)

        group_node = self.create_node("group")

        group_label = self.create_node("label")
        if self.entity_read.on_column_show_in_parent():
            repeat_node = self.create_node('repeat')
            ref = 'nodeset'
            repeat_node.setAttribute("appearance", "field-list")
            repeat_node.setAttribute(ref, cate_name)
            repeat_label = self.create_node("label")
            repeat_label.appendChild(dom_text)
            repeat_node.appendChild(repeat_label)
            group_label.appendChild(self.create_text_node(title))
            group_node.appendChild(group_label)
            group_node.appendChild(repeat_node)

        else:
            group_node.setAttribute("appearance", "field-list")
            group_node.setAttribute(ref, cate_name)
            group_label.appendChild(dom_text)
            group_node.appendChild(group_label)
        # label_txt = self.create_text_node(
        #     self.profile_name + ": "+entity.replace("_", " ").title())
        return group_node, repeat_node

    def social_tenure_nodes(self):
        '''
        Format social tenure attributes into a groups. This will enable str definition in mobile from one page
        and it can be repeated if there are multiple entities for creating str.
        :return:
        '''
        repeat_node = None
        ref = 'ref'
        entity = 'social_tenure'
        label_txt = self.create_text_node('Social Tenure Relationship')
        cate_name = self.model_category_group(self.profile_name,
                                              entity)
        group_node = self.create_node("group")
        group_label = self.create_node("label")
        if not self.check_str_supports_multiple_entities():
            group_node.setAttribute("appearance", "field-list")
            group_node.setAttribute(ref, cate_name)
            group_label.appendChild(label_txt)
            group_node.appendChild(group_label)

        elif self.check_str_supports_multiple_entities():
            repeat_node = self.create_node('repeat')
            ref = 'nodeset'
            cate_name = self.model_category_group(self.profile_name, 'social_tenure')
            repeat_node.setAttribute("appearance", "field-list")
            repeat_node.setAttribute(ref, cate_name)
            str_label = self.create_node("label")
            str_label.appendChild(label_txt)

            group_label.appendChild(self.create_text_node(
                'Social Tenure Relationship'))
            repeat_node.appendChild(str_label)
            group_node.appendChild(group_label)
            group_node.appendChild(repeat_node)
        return group_node, repeat_node

    def check_str_supports_multiple_entities(self):
        '''
        We want str to create multiple forms only when its has multiple 
        entities participating in STR else, we make a simple one that is 
        not repeating
        '''
        has_multiple = False
        # party_tbl = self.entity_read.social_tenure().parties
        # spunit_tbl = self.entity_read.social_tenure().spatial_units
        party_tbl = current_profile().social_tenure.parties
        spunit_tbl = current_profile().social_tenure.spatial_units
        if len(party_tbl) > 1 or len(spunit_tbl) > 1:
            has_multiple = True
        return has_multiple

    def _body_section_data(self, reader: GeoODKReader, entity_values: dict, parent_node: QDomElement):
        """
        Add entity attributes to the body section as labels to the Xform file
        Create label fields to the input fields
        :return:
        """
        #parent_path = self.profile_name + "/" + self.entity_read.default_entity()
        parent_path = self.profile_name + "/" + reader.default_entity()
        for key in entity_values.keys():
            if reader.is_lookup_column(key):
                self.format_lookup_data(key, parent_node)
            else:
                body_node = self.create_node("input")
                label_node = self.create_node("label")
                body_node.setAttribute("ref", self.model_category_group(parent_path, key))

                label_text_info = reader.col_label(key)
                label_txt = self.create_text_node(label_text_info)
                # label_node.setAttribute("ref", label)
                label_node.appendChild(label_txt)
                body_node.appendChild(label_node)
                parent_node.appendChild(body_node)
        """
        Check if the entity has supporting document
        Document considered at this point, image type
        """
        if reader.entity_has_supporting_documents():
            doc_list = reader.entity_supported_document_types()
            self._supporting_documents_field_labels(doc_list, parent_node, entity=None)

        return parent_node

    def _supporting_documents_field_labels(self, doc_list, parent_node, entity=None):
        """
        Create labels for document capture field so that the user
        Knows what document is capturing
        :param parent_node
        :type string
        :return: node
        :rtype: QDomNode
        """
        if entity == 'social_tenure':
            entity_name = 'social_tenure'
        if not entity:
            entity_name = self.entity_read.default_entity()
            doc_list = self.entity_read.entity_supported_document_types()
        if len(doc_list) < 2:
            doc_node = self.create_node('upload')
            doc_node.setAttribute('mediatype', 'image/*')
            doc_node.setAttribute('ref', self.set_model_xpath(self.supports_doc,
                                                              entity_name))
            label_doc_node = self.create_node('label')
            label_doc_node_text = self.create_text_node(self.supports_doc)
            label_doc_node.appendChild(label_doc_node_text)
            doc_node.appendChild(label_doc_node)
            parent_node.appendChild(doc_node)
        else:
            for doc in doc_list:
                if doc == 'General':
                    continue
                doc_node = self.create_node('upload')
                doc_node.setAttribute('mediatype', 'image/*')
                doc_node.setAttribute('ref', self.set_model_xpath(doc.replace(' ', '-') + '_' + self.supports_doc,
                                                                  entity_name))
                label_doc_node = self.create_node('label')
                label_doc_node_text = self.create_text_node(doc + '_' + self.supports_doc)
                label_doc_node.appendChild(label_doc_node_text)
                doc_node.appendChild(label_doc_node)
                parent_node.appendChild(doc_node)

    def social_tenure_label(self, parent_node):
        """
        Add social tenure labels on the form
        :param parent_node Qnode
        :return:
        """
        parent_path = self.profile_name + "/" + 'social_tenure'
        doc_list = self.entity_read.profile().social_tenure.document_types_non_hex()
        entity_values = self.entity_read.social_tenure_attributes()
        group_node, rp_node = self.social_tenure_nodes()
        party_tbl = self.entity_read.social_tenure().party_columns
        spunit_tbl = self.entity_read.social_tenure().spatial_unit_columns
        if rp_node:
            self.filter_str_table_in_node_creation(party_tbl, rp_node, 'party')
            self.filter_str_table_in_node_creation(spunit_tbl, rp_node, 'spatial_unit')
        for key in entity_values.keys():
            if self.entity_read.field_is_social_tenure_lookup(key) and rp_node:
                self.format_lookup_for_social_tenure(key, rp_node)
            elif self.entity_read.field_is_social_tenure_lookup(key) and not rp_node:
                self.format_lookup_for_social_tenure(key, group_node)
            else:
                body_node = self.create_node("input")
                label_node = self.create_node("label")
                body_node.setAttribute("ref", self.model_category_group(parent_path, key))

                label_text_info = self.entity_read.col_label(key)
                if label_text_info == '' or label_text_info is None:
                    label_text_info = key.replace('_', ' ').title()
                label_txt = self.create_text_node(label_text_info)
                # label_node.setAttribute("ref", label)
                label_node.appendChild(label_txt)
                body_node.appendChild(label_node)
                if rp_node:
                    rp_node.appendChild(body_node)
                    group_node.appendChild(rp_node)
                else:
                    group_node.appendChild(body_node)
        if rp_node:
            self._supporting_documents_field_labels(doc_list, rp_node, 'social_tenure')
        else:
            self._supporting_documents_field_labels(doc_list, group_node, 'social_tenure')
        parent_node.appendChild(group_node)
        return parent_node

    def filter_str_table_in_node_creation(self, str_entity_tbl, node, label_name):
        '''Lets isolate party and spatial unit tables while creating str in the form so that
        we format them in a manner that supports multiple str creation on the form
        In this implementation we shall treat them as lookup to allow for flexible selection of party and sp unit
        added in 1.7
        :param str_entity_tbl:   list
        :param node: Qnode
        :param label_node:   str
        :return Qnode '''

        lk_node = self.create_node('select1')
        lk_node.setAttribute("ref", self.set_model_xpath(label_name, 'social_tenure'))
        lk_node_title = self.create_node('label')
        lk_item_title_txt = self.create_text_node('Select {}'.format(label_name))
        lk_node_title.appendChild(lk_item_title_txt)
        lk_node.appendChild(lk_node_title)

        for key in str_entity_tbl:
            lk_item = self.create_node("item")
            lk_item_label = self.create_node("label")
            encode_key = key[:int(key.index('_id'))]
            lk_item_label_txt = self.create_text_node(encode_key.title())
            lk_item_label_txt_val = self.create_node("value")
            lk_item_label_txt_val_txt = self.create_text_node(encode_key)

            lk_item_label.appendChild(lk_item_label_txt)
            lk_item_label_txt_val.appendChild(lk_item_label_txt_val_txt)
            lk_item.appendChild(lk_item_label)
            lk_item.appendChild(lk_item_label_txt_val)
            lk_node.appendChild(lk_item)
            node.appendChild(lk_node)

    def format_lookup_data(self, col, parent_node):
        """
        Loop through the columns and if the column is a lookup
        Format it to the right format in Xform
        :param parent_node: the group holding the children
        :return:
        """
        self.entity_read.read_attributes()
        child_node = self.lookup_formatter(
            self.entity_read.default_entity(), col)
        parent_node.appendChild(child_node)

    def lookup_formatter(self, entity, col):
        """
        Format lookup to the Xform type
        :param lookup: entity name
        :param col: Lookup column
        :return:
        """
        self.entity_read.column_lookup_mapping()
        select_opt = "select1"
        if self.entity_read.column_info_multiselect(col):
            select_opt = "select"
        else:
            select_opt = select_opt
        lk_node = self.create_node(select_opt)
        lk_node.setAttribute("ref", self.set_model_xpath(col, entity))
        lk_node_label = self.create_node("label")
        # lk_node_label_txt = self.create_text_node(
        #     self.entity_read.user_entity_name() + " " +
        #     col.replace("_"," ").title().replace("Id", ""))
        lk_node_label_txt = self.create_text_node(
            self.entity_read.col_label(col))
        lk_node_label.appendChild(lk_node_label_txt)
        lk_node.appendChild(lk_node_label)

        # create lookup element on the form
        self.entity_read.set_user_selected_entity()

        col_obj = self.entity_read.entity_object().columns[col]

        lk_name_values = None
        if isinstance(col_obj, BooleanColumn):
            # Lookup values for yes no have been hardcoded
            lk_name_values = self.yes_no_list()
        else:
            # Read lookup from configuration
            lk_name_values = self.entity_read.format_lookup_items(col)
        if lk_name_values:
            self.lookup_value_list(lk_node, lk_name_values)
        return lk_node

    def lookup_value_list(self, lookupnode, value_list):
        """
        Add lookup value list in the form as choices in the form field
        :param lookupnode:string
        :param value_list:dict
        :return: node
        """
        for key, val in value_list.items():

            lk_item = self.create_node("item")
            lk_item_label = self.create_node("label")
            # encode_key = key.encode('utf_8')
            lk_item_label_txt = self.create_text_node(key)
            lk_item_label_txt_val = self.create_node("value")
            if val == "":
                val = key
            lk_item_label_txt_val_txt = self.create_text_node(val)

            lk_item_label.appendChild(lk_item_label_txt)
            lk_item_label_txt_val.appendChild(lk_item_label_txt_val_txt)

            lk_item.appendChild(lk_item_label)
            lk_item.appendChild(lk_item_label_txt_val)
            lookupnode.appendChild(lk_item)
        return lookupnode

    def format_lookup_for_social_tenure(self, key, parent):
        """
        Get social tenure lookup values for the given column
        Since social tenure is not treated as an entity, we have to call it values separately
        :return:
        """
        lk_node = self.create_node('select1')
        lk_node.setAttribute("ref", self.set_model_xpath(key, 'social_tenure'))
        lk_node_label = self.create_node("label")
        label_text = self.entity_read.col_label(key)
        if label_text == '' or label_text is None:
            label_text = key.replace("_", ' ').title()
        lk_node_label_txt = self.create_text_node(label_text)

        lk_node_label.appendChild(lk_node_label_txt)
        lk_node.appendChild(lk_node_label)

        str_lookup_attributes = self.entity_read.social_tenure_lkup_from_col(key)
        self.lookup_value_list(lk_node, str_lookup_attributes)
        parent.appendChild(lk_node)
        # return lk_node

    def write_data_to_xform(self) -> tuple[bool, str]:
        if self.form is None:
            return False, "Error: No file to write data!"

        if not isinstance(self.form, QFile):
            return False, "Error: Output file not supported!"

        # get all the document node and write the data to file
        root_node = self.create_xform_root_node()
        root_node.appendChild(self.header_fragment_data())
        root_node.appendChild(self._body_section())
        self.doc.appendChild(root_node)

        written_bytes = self.write_to_file(self.form, self.doc)

        if written_bytes < 0:
            return False, "Error: Error occurred while writting data to file."

        return True, "Total bytes written {}".format(written_bytes)
