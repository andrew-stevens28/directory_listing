import threading, time, os, re
from PySide.QtUiTools import *

#from PySide.QtCore import QThread, QMutex, QObject, Signal
from PySide.QtCore import *
#from PySide.QtGui import *
from dir_listing import DirectoryListing

#class OutputSignal(QObject):
#  #sig = Signal(list)
#  sig = SIGNAL("displayOutput(QString)")

#class FinishedSignal(QObject):
#  #sig = Signal(list)
#  sig = SIGNAL("Finished")

class ProcessWorker(QThread):
  def __init__(self, parent=None):
    QThread.__init__(self, parent)
    self.stopped = False
    self.mutex = QMutex()
    self.path = None
    self.output = []
    self.checkType = ''
    self.dirListSaveDir = ''
    self.prefix = ''
    #self.signal = OutputSignal()
    #self.sig_finished = FinishedSignal()
    self.listing = DirectoryListing()

  def initialize(self, path, checkType='', dirListSaveDir='', prefix=''):
    self.stopped = False
    self.path = path
    self.completed = False
    self.output = []
    self.checkType = checkType
    self.dirListSaveDir = dirListSaveDir
    self.prefix = prefix

  def run(self):
    num_jobs = self.getNumJobs()
    #print "number of jobs to do: %d" % num_jobs
    self.emit(SIGNAL("setProgressBar%s(int)" % self.checkType ), num_jobs)
    self.output = self.listing.list_directories(self.path)
    #self.stopped = True
    #self.stop()
    #self.emit(SIGNAL("finished(bool)"), self.completed)
    #return output
    #print "number of jobs returned: %d" % len(self.output)
    if not self.output == []:
      for out in self.output:
        #self.signal.sig.emit(out)
        self.emit(SIGNAL("display%sOutput(QString)" % self.checkType), out)
      #print self.dirListSaveDir, self.prefix
      if not self.dirListSaveDir == '':
        #print "writing file..."
        self.listing.write_output_to_file(self.dirListSaveDir, self.prefix, self.output)
      self.emit(SIGNAL('finished%s(QString)' % self.checkType), 'done')
    else:
      #print "emitting that we have finished with a terminated value"
      self.emit(SIGNAL('finished%s(QString)' % self.checkType), 'terminated')
    #self.sig_finished.sig.emit()

  def stop(self):
    with QMutexLocker(self.mutex):
      self.stopped = True
      self.listing.stop()

  def getNumJobs(self):
    num_jobs = 0
    for root, dirs, files in os.walk(self.path, followlinks=True):  #since os.walk returns a tuple, we traverse the tuple and grab the 3 attributes of each directory
      if not files == []:
        num_jobs += 1
    return num_jobs

  def reset(self):
    with QMutexLocker(self.mutex):
      self.stopped = False
      self.listing.resetExitFlag()
    
  def isStopped(self):
    with QMutexLocker(self.mutex):
      if self.stopped:
        return
