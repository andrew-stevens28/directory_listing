#!/usr/bin/env python

import sys
from PySide.QtUiTools import *

#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PySide.QtCore import *
from PySide.QtGui import *
from time import time, sleep

#from dir_listing import *
from process_thread import ProcessWorker

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

    ## initialize the thread here
    self.workerThread = ProcessWorker()

    self.myWidget.setMinimumSize(985,850)
    layout = QVBoxLayout()
    layout.addWidget(self.myWidget)
    self.setLayout(layout)
    self.progMax = 0
    #self.myWidget.setupUi()

    #avail_widgets = loader.availableWidgets()
    #avail_widgets = self.myWidget.findChildren(QPushButton)

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
    self.myWidget.findChild(QPushButton,'cancelPushButton').clicked.connect(self.cancelDirectoryListing)
    self.myWidget.findChild(QCheckBox,'addPrefixCheckBox').stateChanged.connect(self.setPrefixLineEdit)
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').valueChanged.connect(self.setProgressBar)
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').valueChanged.connect(self.updateProgressBar)
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').hide()
    self.myWidget.findChild(QLabel,'dirListingProgressTypeLabel').hide()
    self.myWidget.findChild(QLabel,'dirListingProgressLabel').hide()
    if self.myWidget.findChild(QPushButton,'cancelPushButton').isEnabled():
      self.myWidget.findChild(QPushButton,'cancelPushButton').setEnabled(False)

    # directory listing and file check pushbuttons and checkboxes and labels
    self.myWidget.findChild(QPushButton,'sourceDirCheckPushButton').clicked.connect(self.selectSourceDirCheckDirectory)
    self.myWidget.findChild(QPushButton,'destDirCheckPushButton').clicked.connect(self.selectDestDirCheckDirectory)
    self.myWidget.findChild(QPushButton,'dirListingDirCheckFileSavePushButton').clicked.connect(self.selectDirListingDirCheckFileSaveDirectory)
    self.myWidget.findChild(QCheckBox,'addPrefixDirCheckCheckBox').stateChanged.connect(self.setPrefixDirCheckLineEdit)
    self.myWidget.findChild(QPushButton,'createDirCheckPushButton').clicked.connect(self.createDirectoryListingDirCheck)
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').valueChanged.connect(self.setProgressBarDirCheck)
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').valueChanged.connect(self.updateProgressBarDirCheck)
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').hide()
    self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').hide()
    self.myWidget.findChild(QLabel,'dirListingDirCheckProgressTypeLabel').hide()
    self.myWidget.findChild(QPushButton,'clearDirCheckPushButton').clicked.connect(self.clearDirCheckOutputTextEdit)
    if self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').isEnabled():
      self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').setEnabled(False)

    ## handlers for thread
    #self.workerThread.signal.sig.connect(self.workerThreadFinished)
    self.connect(self.workerThread, SIGNAL('displayOutput(QString)'), self.workerThreadPrintOutput)
    self.connect(self.workerThread, SIGNAL('finished(QString)'), self.workerThreadFinished)
    self.connect(self.workerThread, SIGNAL('setProgressBar(int)'), self.setProgressBar)

    ##handlers for thread to display output to the dirCheck tab
    self.connect(self.workerThread, SIGNAL('displayDirCheckOutput(QString)'), self.workerThreadPrintDirCheckOutput)
    self.connect(self.workerThread, SIGNAL('finishedDirCheck(QString)'), self.workerThreadDirCheckFinished)
    self.connect(self.workerThread, SIGNAL('setProgressBarDirCheck(int)'), self.setProgressBarDirCheck)
    #self.sig_finished.sig.emit()
    #self.workerThread.signal.sig.connect(self.workerThreadPrintOutput)

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

  def cancelDirectoryListing(self):
    if self.workerThread.isRunning():
      self.workerThread.stop()
    #pass

  def createDirectoryListing(self):
    dirListSaveDir = ""
    prefix = ""
    if self.myWidget.findChild(QLineEdit, 'sourceLineEdit').text() == "":
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Critical)
      msgBox.setText("There was no source directory to list, please select a directory to list and try again")
      msgBox.exec_()
      return
    else:
      directory = self.myWidget.findChild(QLineEdit, 'sourceLineEdit').text()

    if self.myWidget.findChild(QLineEdit,'prefixLineEdit').isEnabled():
      prefix = self.myWidget.findChild(QLineEdit, 'prefixLineEdit').text()

    ## bringing up the progress bar and its label so the user can see it
    if self.myWidget.findChild(QProgressBar,'dirListingProgressBar').isHidden():
      self.myWidget.findChild(QProgressBar,'dirListingProgressBar').show()
    if self.myWidget.findChild(QLabel,'dirListingProgressLabel').isHidden():
      self.myWidget.findChild(QLabel,'dirListingProgressLabel').show()

    self.myWidget.findChild(QLabel,'dirListingProgressLabel').setText("Progress:")
    #self.myWidget.findChild(QProgressBar,'dirListingProgressBar').reset()
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setRange(0,100)
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(1)
    #self.updateProgressBar(1)

    if not self.myWidget.findChild(QLineEdit,'dirListingFileSaveLineEdit').text() == "":
      dirListSaveDir = self.myWidget.findChild(QLineEdit,'dirListingFileSaveLineEdit').text()
    # get the time before the list directory started
    #start_proc = time()
    #output = list_directories(directory)

    ## setting up thread stuff here
    if not self.workerThread.isRunning():
      #print dirListSaveDir, prefix
      self.workerThread.stopped = False
      self.workerThread.initialize(directory, dirListSaveDir=dirListSaveDir, prefix=prefix)
      #self.workerThread.initialize(directory)
      self.workerThread.start()
      self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("Directory listing has started, please wait...\n")
      self.myWidget.findChild(QPushButton,'createPushButton').setEnabled(False)
      if not self.myWidget.findChild(QPushButton,'cancelPushButton').isEnabled():
        self.myWidget.findChild(QPushButton,'cancelPushButton').setEnabled(True)

    # and we get the end time of the process
    #end_proc = time()
    
    #for out in output:
    #  self.myWidget.findChild(QTextEdit, 'outputTextEdit').append(out)

    #print "it took: %f to process the listing" % (end_proc - start_proc)

    #if dirListSaveDir:
    #  write_output_to_file(dirListSaveDir, prefix, output)
    #self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("creating directory listing....")

  # create directory listing for the Directory listing and check tab
  def createDirectoryListingDirCheck(self):
    dirListSaveDir = ""
    prefix = ""
    if self.myWidget.findChild(QLineEdit, 'sourceDirCheckLineEdit').text() == "":
      msgBox = QMessageBox()
      msgBox.setIcon(QMessageBox.Critical)
      msgBox.setText("There was no source directory to list, please select a directory to list and try again")
      msgBox.exec_()
      return
    else:
      directory = self.myWidget.findChild(QLineEdit, 'sourceDirCheckLineEdit').text()
    if not self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text() == "":
      dirListSaveDir = self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text()

    ## getting the prefix for the directory listing file
    if self.myWidget.findChild(QLineEdit,'prefixDirCheckLineEdit').isEnabled():
      prefix = self.myWidget.findChild(QLineEdit, 'prefixDirCheckLineEdit').text()

    self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append("creating directory listing....")

    ## bringing up the progress bar and its label so the user can see it
    if self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').isHidden():
      self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').show()
    if self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').isHidden():
      self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').show()

    self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').setText("Progress:")
    #self.myWidget.findChild(QProgressBar,'dirListingProgressBar').reset()
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setRange(0,100)
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setValue(1)
    #self.updateProgressBar(1)

    if not self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text() == "":
      dirListSaveDir = self.myWidget.findChild(QLineEdit,'dirListingDirCheckFileSaveLineEdit').text()
    # get the time before the list directory started
    #start_proc = time()
    #output = list_directories(directory)

    ## setting up thread stuff here
    if not self.workerThread.isRunning():
      self.workerThread.stopped = False
      self.workerThread.initialize(directory, 'DirCheck', dirListSaveDir, prefix)
      self.workerThread.start()
      self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append("Directory listing has started, please wait...\n")
      self.myWidget.findChild(QPushButton,'createDirCheckPushButton').setEnabled(False)
      if not self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').isEnabled():
        self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').setEnabled(True)


  ## method to set the maximum value of the progress bar
  def setProgressBar(self, maximum):
    #print "the maximum that was emitted: %d" % maximum
    self.progMax = maximum
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setMaximum(maximum)

  ## method to set the maximum value of the progress bar in the DirCheck tab
  def setProgressBarDirCheck(self, maximum):
    #print "the maximum that was emitted: %d" % maximum
    self.progMax = maximum
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setMaximum(maximum)

  ## method to update the progress bar to the job it is at
  def updateProgressBar(self, value):
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(value)

  ## method to update progress bar label
  def updateProgressBarLabel(self, value):
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(value)

  def updateProgressBarDirCheck(self, value):
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setValue(value)

  def workerThreadPrintOutput(self, text):
    self.myWidget.findChild(QTextEdit, 'outputTextEdit').append(text)

  def workerThreadPrintDirCheckOutput(self, text):
    self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append(text)

  #def workerThreadFinished(self, data):
  def workerThreadFinished(self, text):
    if text == 'done':
      self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("Finished Directory listing!\n")
      self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(self.progMax)
      self.myWidget.findChild(QLabel,'dirListingProgressLabel').setText("Complete!!")
    else:
      self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("Directory Listing cancelled!!")
      self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(self.progMax)
      self.myWidget.findChild(QLabel,'dirListingProgressLabel').setText("Cancelled!!")
    print "finished appending data"
    #if not data == []:
    #  for out in data:
    #    self.myWidget.findChild(QTextEdit, 'outputTextEdit').append(out)
    #else:
    #  self.myWidget.findChild(QTextEdit, 'outputTextEdit').append("Directory Listing cancelled!!")

    ## setting the progressbar to the max value as it has finished
      
    self.myWidget.findChild(QPushButton,'createPushButton').setEnabled(True)
    if self.myWidget.findChild(QPushButton,'cancelPushButton').isEnabled():
      self.myWidget.findChild(QPushButton,'cancelPushButton').setEnabled(False)

    self.workerThread.reset()

  def workerThreadDirCheckFinished(self, text):
    if text == 'done':
      self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append("Finished Directory listing!\n")
      self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setValue(self.progMax)
      self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').setText("Complete!!")
    else:
      self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').append("Directory Listing cancelled!!")
      self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setValue(self.progMax)
      self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').setText("Cancelled!!")
    print "finished appending data"

    self.myWidget.findChild(QPushButton,'createDirCheckPushButton').setEnabled(True)
    if self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').isEnabled():
      self.myWidget.findChild(QPushButton,'cancelDirCheckPushButton').setEnabled(False)

    self.workerThread.reset()

  def clearOutputTextEdit(self):
    self.myWidget.findChild(QTextEdit, 'outputTextEdit').clear()
    ##hiding the progress bar and label
    if not self.myWidget.findChild(QProgressBar,'dirListingProgressBar').isHidden():
      self.myWidget.findChild(QProgressBar,'dirListingProgressBar').hide()
      self.updateProgressBar(1)
    if not self.myWidget.findChild(QLabel,'dirListingProgressLabel').isHidden():
      self.myWidget.findChild(QLabel,'dirListingProgressLabel').hide()
      self.myWidget.findChild(QLabel,'dirListingProgressLabel').setText("Progress:")
    self.myWidget.findChild(QProgressBar,'dirListingProgressBar').setValue(1)

  def clearDirCheckOutputTextEdit(self):
    self.myWidget.findChild(QTextEdit, 'outputDirCheckTextEdit').clear()
    ##hiding the progress bar and label
    if not self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').isHidden():
      self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').hide()
      self.updateProgressBar(1)
    if not self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').isHidden():
      self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').hide()
      self.myWidget.findChild(QLabel,'dirListingDirCheckProgressLabel').setText("Progress:")
    self.myWidget.findChild(QProgressBar,'dirListingDirCheckProgressBar').setValue(1)

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
