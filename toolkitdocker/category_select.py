import json
from os import path

from krita import Krita
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from toolkitdocker.json_class import json_class
from toolkitdocker.tool_categories import CategoryDict
from toolkitdocker.toolbuttons import ToolList

category_dictionary = CategoryDict()

class CategorySelect(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.subtool_column = QtWidgets.QVBoxLayout()
        self.columns = QtWidgets.QHBoxLayout()
        self.config_layout = QtWidgets.QVBoxLayout()
        self.header_row = QtWidgets.QHBoxLayout()

        self.preset_dropbox = QtWidgets.QComboBox()
        self.preset_dropbox.insertItem(0, "Painting")
        self.preset_dropbox.setEditable(True)

        self.columns.addLayout(self.subtool_column)

        self.header_row.addWidget(self.preset_dropbox)

        self.config_layout.addLayout(self.header_row)
        self.config_layout.addLayout(self.columns)

        self.containers = {}

        for category in category_dictionary.categories:
            subtool_container = Container(category)

            self.containers.update({category : subtool_container})

        for ToolButton in ToolList:
            tool_panel = ToolPanel()
            tool_panel.setIcon(Krita.instance().icon(ToolButton.icon().name()))
            tool_panel.setObjectName(ToolButton.actionName)
            if ToolButton.isMain == "1":
                self.containers[ToolButton.category].layout().addWidget(tool_panel)
                self.containers[ToolButton.category].layout().addWidget(QVSeparationLine())
            else:
                self.containers[ToolButton.category].layout().addWidget(tool_panel)

        for container in self.containers.values():
            self.subtool_column.addWidget(container)

        self.setLayout(self.config_layout)


class Container(QtWidgets.QFrame):

    def __init__(self, name):
        super().__init__()
        self.name = name
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        self.setLayout(QtWidgets.QHBoxLayout())if isinstance(source, QtWidgets.QWidget):
        self.layout().setAlignment(Qt.AlignmentFlag.AlignLeft) # TOFIX 

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent|None): # pyright: ignore[reportIncompatibleMethodOverride]
        if event is None: return
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent|None): # pyright: ignore[reportIncompatibleMethodOverride]
        if event is None: return
        
        source = event.source()
        if isinstance(source, QtWidgets.QWidget):
            self.layout().addWidget(source) # TOFIX

        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept() # insertWidget

class QVSeparationLine(QtWidgets.QFrame):

  def __init__(self):
    super().__init__()
    self.setFixedWidth(20)
    self.setMinimumHeight(1)
    self.setFrameShape(QtWidgets.QFrame.Shape.VLine)
    self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
    self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)

class ToolPanel(QtWidgets.QToolButton):
    def __init__(self):
        super().__init__()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent|None): # pyright: ignore[reportIncompatibleMethodOverride]
        if event is None: return
        
        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(event.pos() - self.rect().topLeft())

        drag.exec(Qt.DropAction.MoveAction)
