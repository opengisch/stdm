"""
/***************************************************************************
Name                 : TemplateConverter
Description          : Class to convert STDM templates for QGIS2 to QGIS3
Date                 : 01/10/2022
copyright            : (C) 2016 by UN-Habitat and implementing partners.
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

from typing import (
        Type,
        List,
        Dict
 )

from qgis.PyQt.QtCore import (
        QObject,
        QFile,
        QIODevice,
        QDir,
        QDateTime
 )

from qgis.PyQt.QtXml import (
        QDomDocument,
        QDomNode,
        QDomElement
)

from qgis.core import (
        QgsApplication,
        QgsLayout,
        QgsLayoutItem,
        QgsLayoutItemLabel,
        QgsLayoutItemPicture,
        QgsLayoutItemAttributeTable,
        QgsLayoutItemPicture,
        QgsProject,
        QgsPrintLayout,
        QgsReadWriteContext,
        QgsLayoutFrame,
        QgsLayoutMultiFrame,
        QgsLayoutItemMap,
        QgsTask
 )

from stdm.composer.custom_items.label import (
    STDM_DATA_LABEL_ITEM_TYPE
)
from stdm.composer.custom_items.photo import (
    STDM_PHOTO_ITEM_TYPE
)
from stdm.composer.custom_items.chart import (
    STDM_CHART_ITEM_TYPE
)
from stdm.composer.custom_items.table import (
    STDM_DATA_TABLE_ITEM_TYPE
)
from stdm.composer.custom_items.qrcode import (
   STDM_QR_ITEM_TYPE
)
from stdm.composer.custom_items.map import (
        STDM_MAP_ITEM_TYPE
)

from stdm.composer.layout_utils import LayoutUtils

class StreamHandler:
    def log(self, msg: str):
        raise NotImplementedError

class StdOutHandler(StreamHandler):
    def log(self, msg: str):
        print(msg)

class FileHandler(StreamHandler):
    def __init__(self):
        dtime = QDateTime.currentDateTime().toString('ddMMyyyy_HH.MM.ss')
        filename =f'/.stdm/logs/template_converter_{dtime}.log' 
        self.log_file ='{}{}'.format(QDir.home().path(), filename)

    def log(self, msg: str):
        with open(self.log_file, 'a') as lf:
            lf.write(msg)
            lf.write('\n')

class MessageLogger:
    def __init__(self, handler: StreamHandler):
        self.stream_handler = handler()
        self._tag_name = ''

    def log_error(self, msg: str):
        #log_msg = f'{msg}'
        log_msg = '{} [{}]: {}'.format('ERROR', self.tag_name(), msg)
        self.stream_handler.log(log_msg)

    def log_info(self, msg: str):
        #log_msg = f'{msg}'
        log_msg = '{} [{}]: {}'.format('INFO', self.tag_name(), msg)
        self.stream_handler.log(log_msg)

    def set_tag_name(self, tag):
        self._tag_name = tag

    def tag_name(self):
        return self._tag_name

class TemplateConversionError(Exception):
    pass

class TemplateConverterTask(QgsTask):
    def __init__(self, template_path : str): 
        super().__init__('Template Converter Task')
        self.msg_logger = MessageLogger(handler=FileHandler)
        self.msg_logger.set_tag_name('Task')
        self.template_converter = TemplateConverter(folder=template_path, 
                ignore_converted=False, logger=self.msg_logger)

    def run(self):
        is_clean_conversion = self.template_converter.convert()
        if is_clean_conversion:
            msg = self.tr('Template conversion task completed successfully.')
        else:
            msg = self.tr('Template conversion completed but with errors. This log file has details')
        self.msg_logger.log_info(msg)
        return is_clean_conversion


class TemplateConverter(QObject):
    def __init__(self, folder: str='', ignore_converted=True,
            logger=MessageLogger(StdOutHandler)):
        super().__init__(parent=None)
        self._template_folder = folder
        self._ignore_converted = ignore_converted

        self.msg_logger = logger
        
        self._dom_templates = {}

        self.is_clean_conversion = True

        if self._template_folder:
            self._load_templates()

    @property
    def source_folder(self):
        return self._template_folder

    @source_folder.setter
    def source_folder(self, folder: str):
        self._template_folder = folder
        self._load_templates()

    @property
    def v2_templates(self) -> Dict[str, QDomDocument]:
        return self._dom_templates

    def _xml_to_domdoc(self, filename: str):
        xml_file = QFile(filename)
        if not xml_file.open(QIODevice.ReadOnly):
            return (False, None)

        dom_doc = QDomDocument()
        result = dom_doc.setContent(xml_file)
        return result, dom_doc

    def _file_already_converted(self, file: str) -> bool:
        filename =  self._format_template_filename(file)
        full_filename = '{}{}'.format(self._template_folder, filename)
        return QFile.exists(full_filename)

    def _load_templates(self):
        if not self._template_folder:
            return

        files = os.listdir(self._template_folder)
        for file in files:
            if file.endswith('.sdt'):

                if self._ignore_converted:
                    if self._file_already_converted(file):
                        continue

                filename = '{}{}'.format(self._template_folder, file)
                result, dom_doc = self._xml_to_domdoc(filename)
                if not result[0]:
                    err_msg = self.tr('Failed to read the DomDocument `{}`. Error: {}')
                    self.msg_logger.log_error(err_msg.format(file, result[1]))
                    self.is_clean_conversion = False
                    continue
                
                dom_list = dom_doc.elementsByTagName('Composer')  #type: QDomNodeList
                if dom_list.count() > 0:
                    self._dom_templates[file] = dom_doc

    def convert(self) -> bool:
        template_conversion_errors = {}

        for file_name, dom_doc in self._dom_templates.items():
            self.msg_logger.set_tag_name('TemplateConverter')

            init_msg = self.tr('Preparing to convert template')
            self.msg_logger.log_info(f'{init_msg} {file_name}...')

            project = QgsProject().instance()
            layout = QgsPrintLayout(project)
            rw_ctx = QgsReadWriteContext()
            layout.initializeDefaults()

            load_tmpl_msg = self.tr('Loading V2 template to layout')
            self.msg_logger.log_info(f'{load_tmpl_msg}...')

            template_loaded_ok = True
            v2_layout_items, template_loaded_ok = layout.loadFromTemplate(dom_doc, rw_ctx)

            if not template_loaded_ok:
                err_msg = f'Error loading template `{file_name}`. File skipped.'
                self.msg_logger.log_error(err_msg)
                template_conversion_errors[file_name] = 'Error loading template'
                self.is_clean_conversion = 'False'
                continue

            ds_nodes = dom_doc.elementsByTagName('DataSource')  # QDomNodeList
            node_count = ds_nodes.count()
            if node_count == 0:
                msg = self.tr(f'Template data source for file `{file_name}` not found. File skipped.')
                self.msg_logger.log_error(msg)
                template_conversion_errors[file_name] = 'Error template missing data source'
                self.is_clean_conversion = 'False'
                continue

            ds_first_node = ds_nodes.at(0)
            stdm_item_nodes = ds_first_node.childNodes()

            converter_errors = {}

            for n in range(stdm_item_nodes.count()):
                stdm_node = stdm_item_nodes.item(n)
                if stdm_node.isNull():
                    # Log message
                    err_msg = self.tr('Error reading STDM Datasource node item')
                    self.msg_logger.log_error(err_msg)
                    continue
                
                node_name = stdm_node.nodeName()
                converter_cls = BaseLayoutItemConverter.converter_cls_by_node_name(node_name)

                if converter_cls:
                    converter = converter_cls(layout, stdm_node, dom_doc, self.msg_logger)
                    layout_items, conversion_succeded = converter.convert()

                    if not conversion_succeded:
                        if node_name in converter_errors:
                            converter_errors[node_name] += 1
                        else:
                            converter_errors[node_name] = 1

                    self.msg_logger.set_tag_name('TemplateConverter')
                    if len(layout_items) == 0:
                        self.msg_logger.log_info('No {} items to convert.'.format(node_name))
                        continue

                    for layout_item in layout_items:
                        layout.addLayoutItem(layout_item)
                else:
                    self.msg_logger.set_tag_name('TemplateConverter')
                    # Multi-frame converter
                    converter_cls = BaseLayoutItemConverter.multiframe_cls_by_node_name(node_name)

                    if converter_cls is None:
                        converter_msg = self.tr('No converter found for STDM item ')
                        self.msg_logger.log_error(f'{converter_msg} `{node_name}`.')
                        continue

                    converter = converter_cls(layout, stdm_node, dom_doc, self.msg_logger)
                    multiframe_items, conversion_succeded = converter.convert()

                    if not conversion_succeded:
                        if node_name in converter_errors:
                            converter_errors[node_name] += 1
                        else:
                            converter_errors[node_name] = 1

                    self.msg_logger.set_tag_name('TemplateConverter')
                    if len(multiframe_items) == 0:
                            self.msg_logger.log_info('No {} items to convert.'.format(node_name))
                            continue

                    for m_frame in multiframe_items:
                        layout.addMultiFrame(m_frame)
                
                first_ds_node = ds_nodes.at(0)
                datasource_name = first_ds_node.toElement().attribute('name')  #type: str
                referenced_table_name = first_ds_node.toElement().attribute('referencedTable')  #type: str

                self.add_layout_extra_properties(layout, datasource_name, referenced_table_name)

                new_filename = self._format_template_filename(file_name)

            self.msg_logger.set_tag_name('TemplateConverter')
            full_filename = '{}{}'.format(self._template_folder, new_filename)

            if self.write_file(layout, rw_ctx, full_filename):
                file_created_msg = self.tr('File `{}` created successfully.'.format(new_filename))
                self.msg_logger.log_info(file_created_msg)
            else:
                file_created_msg = self.tr('Failed to create file `{}`'.format(new_filename))
                self.msg_logger.log_error(file_created_msg)

            if len(converter_errors) > 0:
                self.is_clean_conversion = False

        return self.is_clean_conversion

    def _format_template_filename(self, filename: str) -> str:
        name, ext = (*filename.rsplit('.', maxsplit=1),)
        return f'{name}_v3.{ext}'


    def add_layout_extra_properties(self, layout: QgsLayout, datasource_name:str,
                                    referenced_table_name: str):
        extra_msg = self.tr('Adding extra layout properties ')
        self.msg_logger.log_info(f'{extra_msg} - [{datasource_name}, {referenced_table_name}].')
        LayoutUtils.set_stdm_data_source_for_layout(layout, datasource_name)
        LayoutUtils.set_stdm_referenced_table_for_layout(layout, referenced_table_name)

    def write_file(self, layout: QgsLayout, rw_context : QgsReadWriteContext ,filename: str) -> bool:
        save_msg = self.tr('Saving layout to file ')
        self.msg_logger.log_info(f'{save_msg} `{filename}`.')
        saved = layout.saveAsTemplate(filename, rw_context)
        return saved


class BaseLayoutItemConverter(QObject):
    NODE_NAME = ''
    registry = {}
    multiframe_registry = {}

    def __init__(self, layout: QgsLayout, node: QDomNode, document: QDomDocument, logger: MessageLogger):
        super().__init__(parent=None)
        self._layout = layout
        self._item_node = node
        self._source_document = document
        self._logger = logger

    @property
    def layout(self) -> QgsLayout:
        return self._layout

    @property
    def node(self) -> QDomNode:
        return self._item_node

    @property
    def  document(self) -> QDomDocument:
        return self._source_document

    @property
    def node_name(self) -> str:
        return BaseLayoutItemConverter.NODE_NAME

    def log_info(self, msg: str):
        #info_msg = '{} [{}]: {}'.format('INFO', self._logger.tag_name(), msg)
        self._logger.log_info(msg)

    def log_error(self, msg: str):
        #error_msg = '{} [{}]: {}'.format('INFO', self._logger.tag_name(), msg)
        self._logger.log_error(msg)

    def set_logger_tag_name(self, tag: str):
        self._logger.set_tag_name(tag)

    @classmethod
    def register(cls):
        if not issubclass(cls, BaseLayoutItemConverter):
            raise TypeError('Invalid layout item converter')

        if not cls.NODE_NAME:
            raise ValueError('Node name is missing')

        BaseLayoutItemConverter.registry[cls.NODE_NAME] = cls

    @classmethod
    def register_multiframe(cls):
        if not issubclass(cls, BaseLayoutItemConverter):
            raise TypeError('Invalid layout item converter')

        if not cls.NODE_NAME:
            raise ValueError('Node name is missing')

        BaseLayoutItemConverter.multiframe_registry[cls.NODE_NAME] = cls

    @classmethod
    def converter_cls_by_node_name(self, node_name: str) -> 'BaseLayoutItemConverter':
        return BaseLayoutItemConverter.registry.get(node_name, None)

    @classmethod
    def multiframe_cls_by_node_name(self, node_name: str) -> 'BaseLayoutItemConverter':
        m_cls = BaseLayoutItemConverter.multiframe_registry.get(node_name, None)
        return m_cls


    def convert(self) -> List[QgsLayoutItem]:
        raise NotImplementedError

    def convert_multiframe(self) ->List[QgsLayoutMultiFrame]:
        raise NotImplementedError


class DataLabelItemConverter(BaseLayoutItemConverter):
    NODE_NAME = 'DataField'

    def convert(self) -> List[QgsLayoutItemLabel]:
        self.set_logger_tag_name(DataLabelItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'Data Label Converter... {STDM_DATA_LABEL_ITEM_TYPE}')
        self.log_info(conv_msg)

        label_items = []

        layout_item_registry = QgsApplication.instance().layoutItemRegistry()
        stdm_label_metadata = layout_item_registry.itemMetadata(STDM_DATA_LABEL_ITEM_TYPE)
        stdm_label_item = stdm_label_metadata.createItem(self.layout)

        element = self.node.toElement()
        
        element_id = element.attribute('itemid','None')
        prev_v2_item = self.layout.itemById(element_id)

        if prev_v2_item is None:
            id_msg = self.tr('Previous data label Item with id {} not found.'.format(
                element_id))
            self.log_error(id_msg)
            return label_items, False

        field_name = element.attribute('name', '')
        if not field_name:
            name_msg = self.tr('Missing field name for STDM label item')
            self.log_error(name_msg)
            is_clean_conversion = False
 
        stdm_label_item.set_linked_field(field_name)
        stdm_label_item.setText(prev_v2_item.text())
        stdm_label_item.setId(stdm_label_item.uuid())
        stdm_label_item.attemptMove(prev_v2_item.positionWithUnits())
        stdm_label_item.attemptResize(prev_v2_item.sizeWithUnits())

        self.layout.removeLayoutItem(prev_v2_item)

        label_msg = self.tr('Created STDM Data Label item.')
        self.log_info(label_msg)

        label_items.append(stdm_label_item)

        return label_items, is_clean_conversion

DataLabelItemConverter.register()

class PhotoItemConverter(BaseLayoutItemConverter):
    NODE_NAME = 'Photos'

    def convert(self) -> List[QgsLayoutItemPicture]:
        self.set_logger_tag_name(PhotoItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'Photo item Converter... {STDM_PHOTO_ITEM_TYPE}')
        self.log_info(conv_msg)
        photo_items = []

        layout_item_registry = QgsApplication.instance().layoutItemRegistry()
        photo_nodes = self.node.childNodes()

        for i in range(photo_nodes.count()):
            photo_node = photo_nodes.item(i)
            element = photo_node.toElement()

            stdm_photo_metadata = layout_item_registry.itemMetadata(STDM_PHOTO_ITEM_TYPE)
            stdm_photo_item = stdm_photo_metadata.createItem(self.layout)

            stdm_photo_item.setId(stdm_photo_item.uuid())
            stdm_photo_item.set_linked_table(element.attribute('table'))
            stdm_photo_item.set_source_field(element.attribute('referenced_field'))
            stdm_photo_item.set_linked_column(element.attribute('referenced_field'))
            stdm_photo_item.set_document_type_id(element.attribute('documentTypeId'))
            stdm_photo_item.set_document_type(element.attribute('documentType'))
            stdm_photo_item.set_referencing_field(element.attribute('referencing_field'))

            item_id = element.attribute('itemid')

            prev_v2_item = self.layout.itemById(item_id)
            if prev_v2_item is None:
                id_msg = self.tr('Previous photo item with id {} not found.'.format(
                    item_id))
                self.log_error(id_msg)
                is_clean_conversion = False
                continue

            stdm_photo_item.attemptMove(prev_v2_item.positionWithUnits())
            stdm_photo_item.attemptResize(prev_v2_item.sizeWithUnits())
            stdm_photo_item.setPicturePath(prev_v2_item.picturePath())

            photo_items.append(stdm_photo_item)

            photo_created_msg = self.tr('Photo item id {} created'.format(
                stdm_photo_item.id()))
            self.log_info(photo_created_msg)

            self.layout.removeLayoutItem(prev_v2_item)

        return photo_items, is_clean_conversion
 
PhotoItemConverter.register()

class ChartItemConverter(BaseLayoutItemConverter):
    NODE_NAME  = 'Charts'

    def convert(self) -> List[QgsLayoutItemPicture]:
        self.set_logger_tag_name(ChartItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'Chart item Converter... {STDM_CHART_ITEM_TYPE}')
        self.log_info(conv_msg)
        chart_items = []

        layout_item_registry = QgsApplication.instance().layoutItemRegistry()

        chart_nodes = self.node.childNodes()

        for i in range(chart_nodes.count()):
            chart_node = chart_nodes.item(i)
            element = chart_node.toElement()

            stdm_chart_metadata = layout_item_registry.itemMetadata(STDM_CHART_ITEM_TYPE)
            stdm_chart_item = stdm_chart_metadata.createItem(self.layout)

            stdm_chart_item.setId(stdm_chart_item.uuid())
            stdm_chart_item.set_linked_table(element.attribute('table'))
            stdm_chart_item.set_source_field(element.attribute('referenced_field'))
            stdm_chart_item.set_linked_column(element.attribute('referenced_field'))
            stdm_chart_item.set_referencing_field(element.attribute('referencing_field'))

            item_id = element.attribute('itemid')

            prev_v2_item = self.layout.itemById(item_id)
            if prev_v2_item is None:
                id_msg = self.tr('Previous chart item with id {} not found.'.format(
                    item_id))
                self.log_error(id_msg)
                is_clean_conversion = False
                continue

            stdm_chart_item.attemptMove(prev_v2_item.positionWithUnits())
            stdm_chart_item.attemptResize(prev_v2_item.sizeWithUnits())
            stdm_chart_item.setPicturePath(prev_v2_item.picturePath())

            chart_items.append(stdm_chart_item)

            chart_created_msg = self.tr('Photo item id {} created'.format(
                stdm_chart_item.id()))
            self.log_info(chart_created_msg)

            self.layout.removeLayoutItem(prev_v2_item)

        return chart_items, is_clean_conversion
    
ChartItemConverter.register()

class TableItemConverter(BaseLayoutItemConverter):
    NODE_NAME  = 'Tables'

    def convert(self) -> QgsLayoutItemAttributeTable:
        self.set_logger_tag_name(TableItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'Table item Converter... {STDM_DATA_TABLE_ITEM_TYPE}')
        self.log_info(conv_msg)
        table_items = []

        layout_item_registry = QgsApplication.instance().layoutItemRegistry()

        multi_frames = self.layout.multiFrames()

        qgis_v2_frames = {}
        for multi_frame in multi_frames:
            frames = multi_frame.frames()
            for frame in frames:
                qgis_v2_frames[frame.id()] = frame

        table_nodes = self.node.childNodes()

        for i in range(table_nodes.count()):
            table_node = table_nodes.item(i)
            element = table_node.toElement()

            stdm_table_metadata = layout_item_registry.multiFrameMetadata(STDM_DATA_TABLE_ITEM_TYPE)  #multiFrameMetadata()
            stdm_table_item = stdm_table_metadata.createMultiFrame(self.layout)  # createMultiFrame

            #Log: None existance attribute
            #Log: Empty attribute
            stdm_table_item.set_table(element.attribute('table'))
            stdm_table_item.set_datasource_field(element.attribute('referenced_field'))
            stdm_table_item.set_referencing_field(element.attribute('referencing_field'))

            item_id = element.attribute('itemid')

            if item_id is None:
                id_msg = self.tr('Previous map item with id {} not found.'.format(
                    item_id))
                self.log_error(id_msg)
                is_clean_conversion = False
                continue

            prev_v2_frame = qgis_v2_frames[item_id]

            parent_mframe = prev_v2_frame.multiFrame()

            columns = parent_mframe.columns()

            stdm_table_item.setColumns(columns)

            frame = QgsLayoutFrame(self.layout, stdm_table_item)
            frame.attemptMove(prev_v2_frame.positionWithUnits(), includesFrame=True)
            frame.attemptResize(prev_v2_frame.sizeWithUnits(), includesFrame=True)
            stdm_table_item.addFrame(frame)

            table_items.append(stdm_table_item)

            self.layout.removeLayoutItem(prev_v2_frame)

        return table_items, is_clean_conversion
    
TableItemConverter.register_multiframe()


class MapItemConverter(BaseLayoutItemConverter):
    NODE_NAME = 'SpatialFields'
    
    def convert(self)-> List[QgsLayoutItemMap]:
        self.set_logger_tag_name(MapItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'Map item Converter... {STDM_MAP_ITEM_TYPE}')
        self.log_info(conv_msg)

        map_items = []
        layout_item_registry = QgsApplication.instance().layoutItemRegistry()
        map_nodes = self.node.childNodes()

        for i in range(map_nodes.count()):
            map_node = map_nodes.item(i)
            element = map_node.toElement()

            stdm_map_metadata = layout_item_registry.itemMetadata(STDM_MAP_ITEM_TYPE)
            stdm_map_item = stdm_map_metadata.createItem(self.layout)

            stdm_map_item.setId(stdm_map_item.uuid())
            stdm_map_item.set_geom_type(element.attribute('geomType'))
            stdm_map_item.set_zoom(element.attribute('zoom'))
            stdm_map_item.set_zoom_type(element.attribute('zoomType'))
            stdm_map_item.set_srid(element.attribute('srid'))
            stdm_map_item.set_label_field(element.attribute('labelField'))
            stdm_map_item.set_name(element.attribute('name'))

            item_id = element.attribute('itemid')

            prev_v2_item = self.layout.itemById(item_id)
            if prev_v2_item is None:
                msg = self.tr('Previous map item with id {} not found.'.format(
                        item_id))
                self.log_error(msg)
                is_clean_conversion = False
                continue

            stdm_map_item.attemptMove(prev_v2_item.positionWithUnits())
            stdm_map_item.attemptResize(prev_v2_item.sizeWithUnits())

            map_items.append(stdm_map_item)
            map_created_msg = self.tr('Map item id {} created.'.format(
                    stdm_map_item.id()))
            self.log_info(map_created_msg)

            self.layout.removeLayoutItem(prev_v2_item)

        return map_items, is_clean_conversion

MapItemConverter.register()


class QRCodeItemConverter(BaseLayoutItemConverter):
    NODE_NAME  = 'QRCodes'

    def convert(self) -> List[QgsLayoutItemPicture]:
        self.set_logger_tag_name(QRCodeItemConverter.NODE_NAME)
        is_clean_conversion = True

        conv_msg = self.tr(f'QRCode item Converter QRCode... {STDM_QR_ITEM_TYPE}')
        self.log_info(conv_msg)
        qrcode_items = []

        layout_item_registry = QgsApplication.instance().layoutItemRegistry()

        qrcode_nodes = self.node.childNodes()
        for i in range(qrcode_nodes.count()):
            qrcode_node = qrcode_nodes.item(i)
            element = qrcode_node.toElement()

            item_id = element.attribute('itemid')
            prev_v2_item = self.layout.itemById(item_id)
            if prev_v2_item is None:
                id_msg = self.tr('Previous QRCode item with id {} not found.'.format(item_id))
                self.log_error(id_msg)
                is_clean_conversion = False
                continue

            stdm_qr_metadata = layout_item_registry.itemMetadata(STDM_QR_ITEM_TYPE)
            stdm_qr_item = stdm_qr_metadata.createItem(self.layout)
            stdm_qr_item.setId(stdm_qr_item.uuid())

            stdm_qr_item.set_linked_field(element.attribute('dataSourceField'))

            stdm_qr_item.attemptMove(prev_v2_item.positionWithUnits())
            stdm_qr_item.attemptResize(prev_v2_item.sizeWithUnits())

            qrcode_items.append(stdm_qr_item)

            self.layout.removeLayoutItem(prev_v2_item)

        return qrcode_items, is_clean_conversion
    
QRCodeItemConverter.register()
