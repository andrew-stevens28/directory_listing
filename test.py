#!/usr/bin/env python

import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from dir_listing_gui_qt_v1 import Ui_dialog

class MainWindow(QMainWindow, Ui_dialog):
  def mymethod(self):
    #self.scrollArea.setText('Hello World')
    sys.exit(0)
    #self.textFieldExample.clear()

  def __init__(self):
    QMainWindow.__init__(self)

    #set up the UI
    self.setupUi(self)
    
    QObject.connect(self.pushButton, SIGNAL("released()"), self.mymethod)

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
