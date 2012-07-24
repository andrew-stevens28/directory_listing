from multiprocessing import *
from yaml import load
import Queue, re, os
from PySide.QtUiTools import *
from PySide.QtCore import *

class Worker(Process, QThread):
  def __init__(self, work_queue, result_queue, checkType='', parent=None):
    #initiallise the worker
    #super.__init__(self)
    Process.__init__(self)
    QThread.__init__(self,parent)

    #job management stuff
    self.work_queue = work_queue
    self.result_queue = result_queue
    self.checkType = checkType
    #self.kill_received = False
    #self.terminate = False
    self.formats_file = 'image_formats.yaml'
    self.exit = Event()

    #self.ret_dict = {}

  def stop(self):
    #self.terminate = True
    #self.kill_received = True
    self.exit.set()

  def run(self):
    proc_name = self.name
    #print proc_name
    #while not self.kill_received or not self.terminate:
    while not self.exit.is_set():
      #get a task
      #try:
      #  job = self.work_queue.get_nowait()
      #except Queue.Empty:
      #  break
      #job = self.work_queue.get()
      try:
        #job = self.work_queue.get_nowait()
        job = self.work_queue.get(timeout=5.0)
      except Queue.Empty:
        print "EMPTY QUEUE!!!"
        break
      #print job
      if job is None:
        #received kill command
        print "%s: Exiting..." % proc_name
        #self.work_queue.task_done()
        #self.kill_received = True
        #self.exit.set()
        break
      if not self.exit.is_set():
        (ranges, dir_count, dir_size) = self.get_listings(job[0], job[1], job[2])
        #print ranges
        #ret_dict[root] = [ranges, dir_count, dir_size]
        #store the result
        #print "adding data to queue"
        #print "ranges from worker: %s " % proc_name
        #print ranges
        if not ranges == []:
          self.result_queue.put([job[0], ranges, dir_count, dir_size])
          self.emit(SIGNAL("updateProgressBar%s(int)" % self.checkType ), 1)
          #self.result_queue.cancel_join_thread()
        else:
          break

        # the below is used with JoinableQueue which is buggy in python2.6 so need to wait for later versions
        # before we can use this...
        #self.work_queue.task_done()
        #print "added job to queue and marked as done"
      else:
        print "Worker: %s killed" % proc_name
    #if self.terminate:
    if self.exit.is_set():
      print "Worker: %s terminated" % proc_name
    return

  def get_image_formats(self):
    f = open(self.formats_file, 'r')
    image_f = load(f)
    f.close()
    return image_f

  def get_listings(self, root, files, OS):
    directories = []
    system = OS
    img_formats = self.get_image_formats()
    path = root    #working directory
    dir_size = 0L    #the total size of the current directory
    range_size = 0L    #the total size of the current frame range
    dir_count = 0L ##the total number of files found
    frame_num = re.compile("([\d]+)")
    directories.append(path)
    #path = path + "@"*(len(files[0].split(".")[0])) + ".dpx"
    ranges = []
    #removed_mac_files = []
    #print files
    count = 0
    new_files = sorted(files)
   
    for f in new_files:
      if not self.exit.is_set():
        #if not f.split(".")[-1] in files_check and re.search(search_mac, f)==None and re.search(search_mac2, f)==None:
        #print f
        #if not f.split(".")[-1] in files_check and re.search(search_mac, f)==None:
        #frame_match = frame_num.match(f)
        #f_groups = frame_match.groups()
        f_groups = re.findall(frame_num, f)
        #if f_groups and f.split(".")[-1] in image_format:  # case where we have something with a number in it
        if "." in f and f_groups and f.rindex(f_groups[-1][-1]) == f.rindex(".")-1 and f.split(".")[-1] in img_formats:  # case where we have something with a number in it and the number is next to a dot at the end we hope
          curr_prefix = f.split(f_groups[-1])[0]
          # because the rindex will go to the end and search if there is a number and a dot at the beginning we are screwed....
          if count == 0:
            #print "count is 0"
            #f_frame = ".".join(f.split(".")[:-1])  #grab first frame of the sequence
            #p_frame = f.split(".")[-2]  #grab first frame of the sequence as its the previous frame when count is 0
            f_frame = f.split(f_groups[-1])[0] + f_groups[-1]  #grab first frame of the sequence
            p_frame = f_groups[-1]  #grab first frame of the sequence as its the previous frame when count is 0
            p_prefix = f.split(f_groups[-1])[0]
            p_post = f.split(f_groups[-1])[-1]
            #range_size += float(subprocess.Popen(["du","-sk",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            count +=1
            if new_files.index(f) == len(new_files) - 1:
              if system == "win32":
                range_size += os.lstat(path + "\\" + f).st_size/1L
              else:
                range_size += os.lstat(path + "/" + f).st_size/1L
              dir_size += range_size
              #count += 1
              dir_count += count
              ranges.append([f, count, range_size])
              range_size = 0L
              count = 0
          elif int(f_groups[-1]) - int(p_frame) > 1:
            #range_size += float(subprocess.Popen(["du","-B1",path + "/" + f.split(".")[0] + "." + p_frame + "." + f.split(".")[-1]], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])/1024L
            if system == "win32":
              range_size += os.lstat(path + "\\" + p_prefix + p_frame + p_post).st_size/1L
            else:
              range_size += os.lstat(path + "/" + p_prefix + p_frame + p_post).st_size/1L
            if count > 1:
              ranges.append([f_frame + "-" + p_frame + p_post, count, range_size])
            else:
              ranges.append([f, count, range_size])
            dir_size += range_size
            range_size = 0L
            #l_frame = f.split(".")[0]
            f_frame = f.split(f_groups[-1])[0] + f_groups[-1]  #grab first frame of the sequence
            p_frame = f_groups[-1]  #grab first frame of the sequence as its the previous frame when count is 0
            p_prefix = f.split(f_groups[-1])[0]
            p_post = f.split(f_groups[-1])[-1]
            range_size = 0L
            #range_size += float(subprocess.Popen(["du","-sk",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            dir_count += count
            count += 1
            if new_files.index(f) == len(new_files) - 1:
              if system == "win32":
                range_size += os.lstat(path + "\\" + f).st_size/1L
              else:
                range_size += os.lstat(path + "/" + f).st_size/1L
              dir_size += range_size
              #count += 1
              dir_count += count
              ranges.append([f, count, range_size])
              range_size = 0L
              count = 0
          elif new_files.index(f) == len(new_files) - 1:
            #range_size += float(subprocess.Popen(["du","-B1",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])/1024L
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            dir_size += range_size
            count += 1
            dir_count += count
            if f.split(f_groups[-1])[0] == p_prefix:
              ranges.append([f_frame + "-" + f_groups[-1] + "." + f.split(".")[-1], count, range_size])
            else:
              ranges.append([f, count, range_size])
            range_size = 0L
            count = 0
          else:
            p_frame = f_groups[-1]
            #range_size += float(subprocess.Popen(["du","-B1",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])/1024L
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            count += 1
        else: ##checking if we have anything else and getting their sizes
          if new_files.index(f) == len(new_files) - 1:
            #range_size += float(subprocess.Popen(["du","-B1",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])/1024L
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            dir_size += range_size
            count += 1
            ranges.append([f, count, range_size])
            range_size = 0L
            dir_count += count
            count = 0
          else:
            #range_size += float(subprocess.Popen(["du","-B1",path + "/" + f], stdout=subprocess.PIPE).communicate()[0].strip().split()[0])/1024L
            if system == "win32":
              range_size += os.lstat(path + "\\" + f).st_size/1L
            else:
              range_size += os.lstat(path + "/" + f).st_size/1L
            dir_size += range_size
            count += 1
            ranges.append([f, count, range_size])
            range_size = 0L
            dir_count += count
            count = 0
      else:
        break
    if not self.exit.is_set():
      ranges.append(["total", dir_size])  #lastly we add the total size to the dictionary
      return (ranges, dir_count, dir_size)
    else:
      #print "cancelling current listing"
      return ([], 0, 0)
