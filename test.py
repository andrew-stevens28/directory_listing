#!/usr/bin/env python

import sys
from PySide.QtUiTools import *

#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PySide.QtCore import *
from PySide.QtGui import *

from dir_listing import *

#from dir_listing_gui_qt_v1 import Ui_dialog

class MainWindow(QWidget):
  def mymethod(self):
    #self.scrollArea.setText('Hello World')
    sys.exit(0)
    #self.textFieldExample.clear()

  def __init__(self, parent=None):
    #QMainWindow.__init__(self)
    #super(QWidget, self).__init__(parent)
    QWidget.__init__(self,parent)
    loader = QUiLoader()

    #set up the UI
    # self.setupUi(self)
    f = QFile("dir_listing_gui.ui")
    f.open(QFile.ReadOnly)
    self.myWidget = loader.load(f)
    f.close()

    #self.setCentralWidget(self.myWidget)

    self.myWidget.setMinimumSize(985,850)
    layout = QVBoxLayout()
    layout.addWidget(self.myWidget)
    self.setLayout(layout)
    #self.myWidget.setupUi()

    #avail_widgets = loader.availableWidgets()
    avail_widgets = self.myWidget.findChildren(QPushButton)

    self.setWidgetProperties()
    #QObject.connect(self.pushButton, SIGNAL("released()"), self.mymethod)
    #QObject.connect(myWidget.pushButton, SIGNAL("released()"), self.mymethod)
    #quit_button = self.myWidget.findChild(QPushButton, 'Quit')
    QObject.connect(self.myWidget.findChild(QPushButton, 'quitPushButton'), SIGNAL("released()"), self.mymethod)

  def setWidgetProperties(self):
    # directory listing tab pushbuttons and checkboxes
    self.myWidget.findChild(QPushButton,'sourcePushButton').clicked.connect(self.selectSourceDirectory)
    self.myWidget.findChild(QPushButton,'dirListingFileSavePushButton').clicked.connect(self.selectDirListingFileSaveDirectory)
    self.myWidget.findChild(QPushButton,'createPushButton').clicked.connect(self.createDirectoryListing)
    self.myWidget.findChild(QPushButton,'clearPushButton').clicked.connect(self.clearOutputTextEdit)
    self.myWidget.findChild(QCheckBox,'addPrefixCheckBox').stateChanged.connect(self.setPrefixLineEdit)
    # directory listing and file check pushbuttons and checkboxes
    self.myWidget.findChild(QPushButton,'sourceDirCheckPushButton').clicked.connect(self.selectSourceDirCheckDirectory)
    self.myWidget.findChild(QPushButton,'destDirCheckPushButton').clicked.connect(self.selectDestDirCheckDirectory)
    self.myWidget.findChild(QPushButton,'dirListingDirCheckFileSavePushButton').clicked.connect(self.selectDirListingDirCheckFileSaveDirectory)
    self.myWidget.findChild(QCheckBox,'addPrefixDirCheckCheckBox').stateChanged.connect(self.setPrefixDirCheckLineEdit)
    self.myWidget.findChild(QPushButton,'createDirCheckPushButton').clicked.connect(self.createDirectoryListingDirCheck)
    self.myWidget.findChild(QPushButton,'clearDirCheckPushButton').clicked.connect(self.clearOutputDirCheckTextEdit)

  def selectSourceDirectory(self):
    self.myWidget.findChild(QLineEdit,'sourceLineEdit').setText(QFileDialog.getExistingDirectory())

  # open a directory dialog box for the source directories of the Directory Listing and Check tab
  def selectSourceDirCheckDirectory(self):
    self.myWidget.findChild(QLineEdit,'sourceDirCheckLineEdit').setText(QFileDialog.getExistingDirectory())

  # open a directory dialog box for the destination directory (where the files were copied to) of the Directory Listing and Check tab
  def selectDestDirCheckDirectory(self):
    self.myWidget.findChild(QLineEdit,'destDirCheckLineEdit').setText(QFileDialog.getExistingDirectory())

  def selectDirListingFileSaveDirectory(self):
    self.myWidget.findChild(QLineEdit,'dirListingFileSaveLineEdit').setText(QFileDialog.getExistingDirectory())

  # open a directory dialog box so user can select a directory to save the dirctory listing to
  def selectDirListingDirCheckFileSaveDirectory(self):
    self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').setText(QFileDialog.getExistingDirectory())

  def setPrefixLineEdit(self):
    if self.myWidget.findChild(QLineEdit,'prefixLineEdit').isEnabled():
      self.myWidget.findChild(QLineEdit,'prefixLineEdit').setEnabled(False)
    else:
      self.myWidget.findChild(QLineEdit,'prefixLineEdit').setEnabled(True)

  # when the 'Add a prefix' checkbox is ticked then enable the textbox so user can enter a prefix
  def setPrefixDirCheckLineEdit(self):
    if self.myWidget.findChild(QLineEdit,'prefixDirCheckLineEdit').isEnabled():
      self.myWidget.findChild(QLineEdit,'prefixDirCheckLineEdit').setEnabled(False)
    else:
      self.myWidget.findChild(QLineEdit,'prefixDirCheckLineEdit').setEnabled(True)

  def createDirectoryListing(self):
    dirListSaveDir = ""
    if self.myWidget.findChild(QLineEdit, 'sourceLineEdit').text() == "":
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Critical)
      msgBox.setText("There was no source directory to list, please select a directory to list and try again")
      msgBox.exec_()
      return
    else:
      directory = self.myWidget.findChild(QLineEdit, 'sourceLineEdit').text()
    if not self.myWidget.findChild(QLineEdit,'dirListingFileSaveLineEdit').text() == "":
      dirListSaveDir = self.myWidget.findChild(QLineEdit,'dirListingFileSaveLineEdit').text()
    (f,output) = list_directories(directory)
    for out in output:
      self.myWidget.findChild(QTextEdit, 'outputTextEdit').append(out)
    #self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("creating directory listing....")

  # create directory listing for the Directory listing and check tab
  def createDirectoryListingDirCheck(self):
    dirListSaveDir = ""
    if self.myWidget.findChild(QLineEdit, 'sourceDirCheckLineEdit').text() == "":
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Critical)
      msgBox.setText("There was no source directory to list, please select a directory to list and try again")
      msgBox.exec_()
      return
    if not self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text() == "":
      dirListSaveDir = self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text()
    self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append("creating directory listing....")

  def clearOutputTextEdit(self):
    self.myWidget.findChild(QTextEdit, 'outputTextEdit').clear()

  # clear the text fromt the texteditor in the 'Directory Listing and Check' tab
  def clearOutputDirCheckTextEdit(self):
    self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').clear()

#Main entry to program. Sets up the main app and create a new window
def main(argv):
  #create Qt application
  app = QApplication(argv, True)
  
  #create main window
  wnd = MainWindow()
  wnd.show()
  
  #connect signal for app finish
  app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
  
  
  # Start the app up
  sys.exit(app.exec_())

if __name__ == '__main__':
  print "we have imported the UI!!!"
  main(sys.argv)
