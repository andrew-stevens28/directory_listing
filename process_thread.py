import threading, time, os, re
from PySide.QtUiTools import *

#from PySide.QtCore import QThread, QMutex, QObject, Signal
from PySide.QtCore import *
#from PySide.QtGui import *
from dir_listing import *

class OutputSignal(QObject):
  sig = Signal(list)

class ProcessWorker(QThread):
  def __init__(self, parent=None):
    QThread.__init__(self, parent)
    self.stopped = False
    self.mutex = QMutex()
    self.path = None
    self.output = []
    self.signal = OutputSignal()

  def initialize(self, path):
    self.stopped = False
    self.path = path
    self.completed = False
    self.output = []

  def run(self):
    self.output = list_directories(self.path)
    #self.stopped = True
    self.stop()
    #self.emit(SIGNAL("finished(bool)"), self.completed)
    #return output
    self.signal.sig.emit(self.output)

  def stop(self):
    with QMutexLocker(self.mutex):
      self.stopped = True
  #  #try:
  #  #  self.mutex.lock()
  #  #  self.stopped = True
  #  #finally:
  #  #  self.mutex.unlock()
    
  def isStopped(self):
    with QMutexLocker(self.mutex):
      if self.stopped:
        return
