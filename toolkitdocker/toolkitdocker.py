"""
Constructs the ToolKit Docker

"""

import json
from os import path

import krita
from krita import Krita
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtWidgets import QStyle

from toolkitdocker.category_select import CategorySelect
from toolkitdocker.flow_layout import FlowLayout
from toolkitdocker.json_class import json_class
from toolkitdocker.tool_categories import CategoryDict
from toolkitdocker.toolbuttons import ToolList

DOCKER_actionName = "ToolKit"
DOCKER_ID = "pykrita_toolkit"


# We need to create instances of these classes to access their functions
jsonMethod = json_class()
category_dictionary = CategoryDict()


# Loads the subtool menu delay time set by user
class delayClass:
    def __init__(self, delayValue: int):
        self.value = delayValue


# Loads the icon size set by user
class iconSizeClass:
    def __init__(self, iconSize: int):
        self.value = iconSize


menu_delayValue = delayClass(jsonMethod.loadJSON()["delayValue"])
menu_iconSizeValue = iconSizeClass(jsonMethod.loadJSON()["iconSize"])


class TKStyle(QtWidgets.QProxyStyle):
    """
    Adjusts how the toolbutton indicator arrow, and delay time are processed by Qt
    Preferences are loaded from data.json via jsonMethod.loadJSON
    """

    def styleHint(self, hint: QStyle.StyleHint, option: QtWidgets.QStyleOption|None, widget: QtWidgets.QWidget|None, returnData: QtWidgets.QStyleHintReturn|None) -> int: # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Changes delay time for toolbutton subtool menu to appear
        """
        if hint == QStyle.StyleHint.SH_ToolButton_PopupDelay:
            return menu_delayValue.value

        return super().styleHint(hint, option, widget, returnData)

    def drawPrimitive(self, element: QStyle.PrimitiveElement, option: QtWidgets.QStyleOption|None, painter: QtGui.QPainter|None, widget: QtWidgets.QWidget|None) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Changes appearance of toolbutton indicator arrow using QPainter
        """
        if element == QStyle.PrimitiveElement.PE_IndicatorArrowDown:
            
            # alternate start point for submenu button mode indicator
            if jsonMethod.loadJSON()["submenuButton"] == True:
                adjusted_point = QtCore.QPointF(2, 7)
            else:
                adjusted_point = QtCore.QPointF(0, 5)

            if option is None: return
            if painter is None: return
            
            triangle = QtGui.QPainterPath()
            startPoint: QPointF = option.rect.bottomRight().toPointF() - adjusted_point
            triangle.moveTo(startPoint)
            triangle.lineTo(startPoint + QPointF(0, 5))
            triangle.lineTo(startPoint + QPointF(-5, 5))
            painter.fillPath(triangle, Qt.GlobalColor.white)

        else:
            super().drawPrimitive(element, option, painter, widget)


class Menu(QtWidgets.QMenu):  # noqa: F821
    """
    Subtools menu for each main toolbutton
    """

    def __init__(self, parent) -> None:
        super().__init__()

        self.parent = parent
        self.setMouseTracking

    def showEvent(self, event: QtGui.QShowEvent|None) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Moves position of menu to top-right toolbutton corner
        """
        super().showEvent(event)

        # Fixes Windows issue of incorrect menu dimensions on secondary displays
        self.windowHandle().setScreen(self.parent().windowHandle())

        self.move(
            self.parent().mapToGlobal(QPointF(0, 0)) + QPointF(self.parent().width(), 0)
        )

    def mouseMoveEvent(self, event: QtGui.QMouseEvent|None): # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Causes the subtool menu to close if cursor exits
        """
        super().mouseMoveEvent(event)

        # boundary area
        buttonTLC = self.parent().geometry().topLeft()
        menuSize = QtCore.QSize(self.geometry().size())
        buttonColumn = QtCore.QRect(buttonTLC, menuSize)

        bounds = self.geometry().united(buttonColumn)

        if bounds.contains(QtGui.QCursor.pos()) == False:
            self.close()


class SettingsWidget(QtWidgets.QWidget):
    """
    Settings interface widget for the user to alter ToolKit layout, and toolbutton properties
    """
    
    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout(self))
        # Create settings tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()

        self.tab1.setLayout(QtWidgets.QVBoxLayout(self))
        self.tab2.setLayout(QtWidgets.QFormLayout(self))

        self.tabs.addTab(self.tab1, "Layout")
        self.tabs.addTab(self.tab2, "General")

        """
        Set up first tab
        """
        # Interface for rearranging toolbutton layout
        self.category_select = CategorySelect()
        self.tab1.layout().addWidget(self.category_select)

        self.tab1.setLayout(self.tab1.layout())

        """
        Set up second tab
        """
        # icon size
        self.iconSizeBox = QtWidgets.QSpinBox()
        self.iconSizeBox.setRange(10, 30)
        self.iconSizeBox.setSingleStep(1)
        self.iconSizeBox.setValue(menu_iconSizeValue.value)
        self.iconSizeBox.setSuffix("px")

        # Create submenu delay time input
        self.subMenuDelay = QtWidgets.QSpinBox()
        self.subMenuDelay.setRange(0, 1000)
        self.subMenuDelay.setSingleStep(100)
        self.subMenuDelay.setValue(menu_delayValue.value)
        self.subMenuDelay.setSuffix("ms")

        # Create submenu button mode toggle
        self.subButtonBox = QtWidgets.QCheckBox()
        self.subButtonBox.setChecked(jsonMethod.existing_data["submenuButton"])

        self.tab2.layout().addRow(Krita.krita_i18n("&Icon Size:"), self.iconSizeBox)
        self.tab2.layout().addRow(Krita.krita_i18n("&Submenu Delay:"), self.subMenuDelay)
        self.tab2.layout().addRow(Krita.krita_i18n("&Submenu Button:"), self.subButtonBox)

        self.tab2.setLayout(self.tab2.layout())

        self.layout().addWidget(self.tabs)

        """
        Add "cancel" and "accept" buttons to main layout
        """
        # Create "OK" button
        self.acceptButton = QtWidgets.QPushButton(Krita.krita_i18n("OK"))
        self.acceptButton.clicked.connect(self.parentWidget().close)
        self.acceptButton.clicked.connect(self.updateSettingsAccept)
        self.acceptButton.clicked.connect(self.changeSubButton)
        self.acceptButton.clicked.connect(jsonMethod.dumpJSON)

        # Create "Cancel" button
        self.cancelButton = QtWidgets.QPushButton(Krita.krita_i18n("Cancel"))
        self.cancelButton.clicked.connect(self.parentWidget().close)

        self.buttons_footer = QtWidgets.QHBoxLayout()

        # Add the buttons to layout
        self.buttons_footer.addItem(QtWidgets.QSpacerItem(80, 0))
        self.buttons_footer.addWidget(self.acceptButton)
        self.buttons_footer.addWidget(self.cancelButton)

        self.layout().addLayout(self.buttons_footer)

        self.setLayout(self.layout())

    def updateSettingsAccept(self):
        """
        Receives and updates the new subtool menu delay value
        """
        menu_delayValue.value = self.subMenuDelay.value()
        jsonMethod.update_dict({"delayValue": menu_delayValue.value})

        # Update the icon size
        menu_iconSizeValue.value = self.iconSizeBox.value()
        jsonMethod.update_dict({"iconSize": menu_iconSizeValue.value})

        for ToolButton in ToolList:
            ToolButton.setStyle(TKStyle("fusion"))
            ToolButton.updateIconSize()  # this isn't updating the icon icon size until restart

    def changeSubButton(self):
        """
        Receives and updates the subtool menu mode
        """
        jsonMethod.update_dict({"submenuButton": self.subButtonBox.isChecked()})


class SDialog(QtWidgets.QDialog):
    """
    Dialog container for Settings interface widget
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ToolKit Settings")
        self.setWindowModality(Qt.WindowModality.WindowModal)

        SLayout = QtWidgets.QGridLayout()

        # Add Settings interface widget
        SLayout.addWidget(SettingsWidget(self))

        self.setLayout(SLayout)


class ToolKitDocker(krita.DockWidget):
    """
    Main ToolKit Docker body, contains the main toolbuttons with subtool menus
    """

    activate_layout = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setFloating(False)
        # Set Docker title in Settings > Dockers
        self.setWindowTitle("ToolKit")

        # Create button group to handle main toolbuttons
        self.mainToolButtons = QtWidgets.QButtonGroup()
        self.mainToolButtons.setExclusive(True)

        # Create settings dialog container
        self.dialog = SDialog()

        # Paint the ToolKitlayout when settings dialog is finalised
        self.dialog.children()[0].acceptButton.clicked.connect(self.setupLayout) # TOFIX

        self.setWidget(QtWidgets.QWidget())

        # Conceal the 'exit' buttons and Docker title with QLabel
        label = QtWidgets.QLabel(" ")

        label.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        label.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        label.setFrameStyle(QtWidgets.QFrame.Shape.Panel | QtWidgets.QFrame.Shadow.Raised)
        label.setMinimumWidth(16)
        label.setFixedHeight(12)

        self.setWidget(self.widget())
        self.setTitleBarWidget(label)

        """
        Initialise ToolKit Docker layout and toolbuttons
        """
        layout = FlowLayout()
        self.widget().setLayout(layout)

        for ToolButton in ToolList:
            category_dictionary.categories[ToolButton.category].addTool(ToolButton)

            ToolButton.setParent(self)

            ToolButton.setStyle(TKStyle("fusion"))

            ToolButton.clicked.connect(self.activateTool)

        # The rest of the layout setup is handled by the "setupLayout" function
        self.activate_layout.connect(self.setupLayout)
        self.activate_layout.emit()

    #        if len(Application.documents()) != 0: # attempted canvas-only mode
    #            QAction(Application.action("view_show_canvas_only")).triggered.connect(self.layout.removeWidget(widget))

    def contextMenuEvent(self, event):
        """
        Shows the Settings dialog on right-click of ToolKit Docker
        """
        super().contextMenuEvent(event)

        self.dialog.exec()

    def activateTool(self):
        """
        Registers and performs the toolbutton's action in Krita
        """
        actionName = self.sender().objectName()
        ac = Krita.instance().action(actionName)

        print(actionName, ac)
        if ac:
            ac.trigger()

        else:
            pass

    def linkMenu(self):
        """
        Populates the toolbutton's menu with subtools from its category
        """
        subMenu = self.sender()

        # Prevent the menu from continuously adding actions every click
        if subMenu.isEmpty():
            categoryName = self.sender().parent().category
            category = category_dictionary.categories[categoryName]

            # Iterate through all the tools in the category
            for key in category.ToolButtons:
                toolIcon = QtGui.QIcon(Krita.instance().icon(category.ToolButtons[key].icon))
                toolText = category.ToolButtons[key].toolName
                toolName = category.ToolButtons[key].actionName
                toolAction = QtGui.QAction(
                    toolIcon, toolText, self
                )  # set up initial toolAction

                # We need to call Krita's shortcut for the toolAction:
                try:
                    Krita.instance().action(toolName).shortcut()

                    # Find the global shortcut
                    toolShortcut = Krita.instance().action(toolName).shortcut().toString()

                    toolAction.setShortcut(toolShortcut)
                except: ... # TOFIX

                toolAction.setObjectName(toolName)
                toolAction.setParent(self.sender().parent())  # set toolbutton as parent

                toolAction.triggered.connect(self.activateTool)  # activate menu tool on click
                toolAction.triggered.connect(self.swapToolButton)

                subMenu.addAction(toolAction)  # add the button for this tool in the menu

            for action in subMenu.actions():  # show tool icons in submenu
                action.setIconVisibleInMenu(True)

    def swapToolButton(self):
        """
        Swaps the clicked subtool with the main toolbutton
        """
        subtool_actionName = self.sender().objectName()

        for ToolButton in ToolList:
            if ToolButton.actionName == subtool_actionName:
                mainToolButton = self.sender().parentWidget() # the current main tool shown

                if mainToolButton.isMain != ToolButton.isMain:
                    mainToolButton.isMain = "0"  # swap the tool's main status
                    ToolButton.isMain = "1"
                    ToolButton.setChecked(True)
                    self.activate_layout.emit()  # recall the setupLayout function
                else:
                    ToolButton.setChecked(True)

    @QtCore.pyqtSlot()
    def setupLayout(self):
        layout = self.widget().layout()

        for ToolButton in ToolList:
            if ToolButton.isMain == "1":  # Add the main tool from each category to the Docker
                self.mainToolButtons.addButton(ToolButton)  # add tool to button group
                layout.addWidget(ToolButton)

                ToolButton.show()

                subMenu = Menu(ToolButton)
                subMenu.setWindowFlags(Qt.WindowType.Popup)

                ToolButton.setMenu(subMenu)  # this will be the submenu for each main tool

                ToolButton.menu().aboutToShow.connect(self.linkMenu)  # Show submenu when clicked

                if jsonMethod.existing_data["submenuButton"] == True:
                    ToolButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                else:
                    ToolButton.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.DelayedPopup)

            else:  # if ToolButton isn't main
                layout.removeWidget(ToolButton)  # remove ToolButton

                ToolButton.close()  # close the toolbutton

        if jsonMethod.loadJSON()["submenuButton"] == True:
            self.setMinimumWidth(40)
        else:
            self.setMinimumWidth(0)

    def canvasChanged(self, canvas): ...


instance = Krita.instance()  # Register as Krita Docker
if instance is not None:
    dock_widget_factory = krita.DockWidgetFactory(
        DOCKER_ID, krita.DockWidgetFactoryBase.DockPosition.DockLeft, ToolKitDocker
    )
    
    instance.addDockWidgetFactory(dock_widget_factory)
