"""
/***************************************************************************
Name                 : STR Nodes
Description          : Module provides classes which act as proxies for
                       representing social tenure relationship information
                       in a QTreeView
Date                 : 10/November/2013 
copyright            : (C) 2013 by John Gitau
email                : gkahiu@gmail.com
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
from collections import OrderedDict
from decimal import Decimal

from PyQt4.QtGui import (
    QIcon,
    QApplication,
    QAction,
    QDialog,
    QMessageBox,
    QMenu,
    QFileDialog,
    QVBoxLayout
)
from PyQt4.QtCore import SIGNAL

from qgis.core import *

from stdm.utils import *

EDIT_ICON = QIcon(":/plugins/stdm/images/icons/edit.png")
DELETE_ICON = QIcon(":/plugins/stdm/images/icons/delete.png")
NO_ACTION_ICON = QIcon(":/plugins/stdm/images/icons/no_action.png")

class BaseSTRNode(object):
    """
    Base class for all STR nodes.
    """
    def __init__(self, data, parent=None, view=None, parentWidget=None,
                 isChild=False, styleIfChild=True, rootDepthForHash=1,
                 model=None):
        self._data = data
        self._children = []
        self._parent = parent
        self._rootNodeHash = ""
        self._view = view
        self._parentWidget = parentWidget
        self._model = model

        if parent is not None:
            parent.addChild(self)
            #Inherit view from parent
            self._view = parent.treeView()
            self._parentWidget = parent.parentWidget()

        '''
        Set the hash of the node that will be taken as the root parent node.
        In this case it will be level one.
        Level zero will not have any hash specified (just be an empty string).
        '''
        if self.depth() == rootDepthForHash:
            self._rootNodeHash = gen_random_string()
        elif self.depth() > rootDepthForHash:
            self._rootNodeHash = self._parent.rootHash()

        #Separator for child text
        self.separator = " : "

        if isChild:
            if styleIfChild:
                self._styleIfChild = True
        else:
            self._styleIfChild = False

        #Default actions that will be most commonly used by the nodes with data management capabilities
        self.editAction = QAction(EDIT_ICON,
                             QApplication.translate("BaseSTRNode","Edit..."),None)
        self.deleteAction = QAction(DELETE_ICON,
                             QApplication.translate("BaseSTRNode","Delete"),None)

        self._expand_action = QAction(QApplication.translate("BaseSTRNode","Expand"),
                                      self._parentWidget)
        self._collapse_action = QAction(QApplication.translate("BaseSTRNode","Collapse"),
                                      self._parentWidget)

    def addChild(self,child):
        '''
        Add child to the parent node.
        '''
        self._children.append(child)

    def insertChild(self,position,child):
        '''
        Append child at the specified position in the list
        '''
        if position < 0 or position > len(self._children):
            return False

        self._children.insert(position, child)
        child._parent = self

        return True

    def removeChild(self,position):
        '''
        Remove child at the specified position.
        '''
        if position < 0 or position >= len(self._children):
            return False

        child = self._children.pop(position)
        child._parent = None

        return True

    def clear(self):
        '''
        Removes all children in the node.
        '''
        try:
            del self._children[:]
            return True
        except:
            return False

    def child(self,row):
        '''
        Get the child node at the specified row.
        '''
        if row < 0 or row >= len(self._children):
            return None

        return self._children[row]

    def childCount(self):
        '''
        Number of children node with the current node as the parent.
        '''
        return len(self._children)

    def children(self):
        '''
        Returns all the node's children as a list.
        '''
        return self._children

    def hasParent(self):
        '''
        True if the node has a parent. Otherwise returns False.
        '''
        return True if self._parent else False

    def parent(self):
        '''
        The parent of this node.
        '''
        return self._parent

    def treeView(self):
        '''
        Returns the tree view that contains this node.
        '''
        return self._view

    def parentWidget(self):
        '''
        Returns the main widget that displays the social tenure relationship information.
        '''
        return self._parentWidget

    def row(self):
        '''
        Return the position of this node in the parent container.
        '''
        if self._parent:
            return self.parent()._children.index(self)

        return 0

    def icon(self):
        '''
        Return a QIcon for decorating the node.
        To be implemented by subclasses.
        '''
        return None

    def id(self):
        '''
        Returns the ID of the model it represents.
        '''
        return -1

    def depth(self):
        '''
        Returns the depth/hierarchy of this node.
        '''
        depth = 0
        item = self.parent()

        while item is not None:
            item = item.parent()
            depth += 1

        return depth

    def rootHash(self):
        '''
        Returns a hash key that is used to identify the lineage of the child nodes i.e.
        which node exactly is the 'forefather'.
        '''
        return self._rootNodeHash

    def styleIfChild(self):
        '''
        Style the parent _title if set to 'True'.
        This is a read only property.
        '''
        return self._styleIfChild

    def data(self, column):
        '''
        Returns the data item in the specified specified column index within the list.
        '''
        if column < 0 or column >= len(self._data):
            raise IndexError

        return self._data[column]

    def setData(self, column, value):
        '''
        Set the value of the node data at the given column index.
        '''
        if column < 0 or column >= len(self._data):
            return False

        self._data[column] = value

        return True

    def model(self):
        """
        :return: Returns the data model associated with this node. Returns
        'None' if not defined.
        :rtype: object
        """
        return self._model

    def columnCount(self):
        '''
        Return the number of columns.
        '''
        return len(self._data)

    def column(self,position):
        '''
        Get the data in the specified column.
        '''
        if position < 0 and position >= len(self._data):
            return None

        return self._data[position]

    def removeColumns(self,position,columns):
        '''
        Removes columns in the STR node.
        '''
        if position < 0 or position >= len(self._data):
            return False

        for c in range(columns):
            self._data.pop(position)

        return True

    def clearColumns(self):
        '''
        Removes all columns in the node.
        '''
        del self._data[:]

    def typeInfo(self):
        return "BASE_NODE"

    def __repr__(self):
        return self.typeInfo()

    def manageActions(self, modelindex, menu):
        """
        Returns the list of actions to be loaded into the context menu
        of this node when a user right clicks in the treeview.
        Default actions are for expanding/collapsing child nodes.
        To be inherited by subclasses for additional custom actions.
        """
        nullAction = QAction(NO_ACTION_ICON,
                             QApplication.translate("BaseSTRNode", "No User Action"),
                             self.parentWidget())
        nullAction.setEnabled(False)

        if not self._view is None:
            if self._view.isExpanded(modelindex):
                self._expand_action.setEnabled(False)
                self._collapse_action.setEnabled(True)

            else:
                self._expand_action.setEnabled(True)
                self._collapse_action.setEnabled(False)

        #Disconnect then reconnect signals
        if self.signalReceivers(self._expand_action) > 0:
            self._expand_action.triggered.disconnect()

        if self.signalReceivers(self._collapse_action) > 0:
            self._collapse_action.triggered.disconnect()
        #str_editor = STREditor(self._model,self)
        #Connect expand/collapse signals to the respective actions
        self._expand_action.triggered.connect(lambda:self._on_expand(modelindex))
        self._collapse_action.triggered.connect(lambda: self._on_collapse(modelindex))
        #self.editAction.triggered.connect(lambda :str_editor.onEdit(modelindex))

        menu.addAction(self._expand_action)
        menu.addAction(self._collapse_action)
        #menu.addAction(self.separator)
        #menu.addAction(self.editAction)

    def _on_expand(self, index):
        """
        Slot raised to expand all children under this node at the specified
        index.
        :param index: Location in the data model.
        :type index: QModelIndex
        """
        if index.isValid():
            self._view.expand(index)

    def _on_collapse(self, index):
        """
        Slot raised to collapse all children under this node at the specified
        index.
        :param index: Location in the data model.
        :type index: QModelIndex
        """
        if index.isValid():
            self._view.collapse(index)

    def onEdit(self,index):
        '''
        Slot triggered when the Edit action of the node is triggered by the user.
        Subclasses to implement.
        '''
        pass

    def onDelete(self,index):
        '''
        Slot triggered when the Delete action of the node is triggered by the user.
        Subclasses to implement.
        '''
        pass

    def signalReceivers(self, action, signal = "triggered()"):
        '''
        Convenience method that returns the number of receivers connected to the signal of the action object.
        '''
        return action.receivers(SIGNAL(signal))

    def _concat_names_values(self, display_mapping, formatter):
        """
        Extract model values based on the properties defined by display mapping
        and concatenates the display-friendly property name with its corresponding
        value.
        :param display_mapping: Collection containing a tuple of column name
        and display name as key and column value.
        :type display_mapping: dict
        :param formatter: Collections of functions mapped to the property names
        that format the corresponding attribute values.
        :type formatter: dict
        :return: list of display name-value pairs.
        :rtype: list
        """
        name_values = []

        for col_name_prop, attr_val in display_mapping.iteritems():
            prop, prop_display = col_name_prop[0], col_name_prop[1]
            if prop in formatter:
                attr_val = formatter[prop](attr_val)

            name_val = "%s: %s" %(prop_display, attr_val)
            name_values.append(name_val)

        return name_values

    def _property_values(self, model, display_mapping, formatter):
        """
        Extract model values based on the properties defined by display_mapping.
        :param model: Instance of database model.
        :param display_mapping: property names and corresponding display-friendly
        names.
        :type display_mapping: dict
        :param formatter: Collections of functions mapped to the property names
        that format the corresponding attribute values.
        :type formatter: dict
        :return: Attribute values as specified in the display_mapping.
        :rtype: list
        """
        attr_values = []

        for prop, disp in display_mapping.iteritems():
            attr_val = getattr(model, prop)

            if prop in formatter:
                attr_val = formatter[prop](attr_val)

            attr_values.append(attr_val)

        return attr_values

    def _display_mapping(self):
        """
        :return: Property names and their corresponding display names.
        :rtype: dict
        """
        raise NotImplementedError

class SupportsDocumentsNode(BaseSTRNode):
    """
    Node for those entities which support documents to be attached.
    """
    def documents(self):
        return []

class EntityNode(SupportsDocumentsNode):
    """
    Node for displaying general information purtaining to an entity.
    """
    def __init__(self, *args, **kwargs):
        self._colname_display_value = args[0]
        is_child = kwargs.get("isChild", False)
        self._parent_header = kwargs.pop("header", "")
        self._value_formatters = kwargs.pop("value_formatters", {})

        if not is_child:
            super(EntityNode, self).__init__(
                self._colname_display_value.values(),
                **kwargs
            )

        else:
            super(EntityNode, self).__init__([self._parent_header], **kwargs)
            self._set_children()

    def icon(self):
        return QIcon(":/plugins/stdm/images/icons/table.png")

    def typeInfo(self):
        return "ENTITY_NODE"

    def _set_children(self):
        """
        Add text information as children to this node displaying more
        information on the given entity.
        """
        prop_val_mapping = self._concat_names_values(self._colname_display_value,
                                                     self._value_formatters)
        for p_val in prop_val_mapping:
            ch_ent_node = BaseSTRNode([p_val], self)
    
class NoSTRNode(BaseSTRNode):
    """
    Node for showing that no STR relationship exists.
    """
    def __init__(self,parent=None):
        noSTRText = unicode(QApplication.translate("NoSTRNode",
                                                   "No STR Defined"))

        super(NoSTRNode,self).__init__([noSTRText],parent)
        
    def icon(self):
        return QIcon(":/plugins/stdm/images/icons/remove.png")
    
    def typeInfo(self):
        return "NO_STR_NODE"

class STRNode(EntityNode):
    """
    Node for rendering STR information.
    """
    def icon(self):
        return QIcon(":/plugins/stdm/images/icons/social_tenure.png")

class SpatialUnitNode(EntityNode):
    """
    Node for rendering spatial unit information.
    """
    def icon(self):
        return QIcon(":/plugins/stdm/images/icons/layer.gif")


    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        