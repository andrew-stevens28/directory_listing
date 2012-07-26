from multiprocessing import *
from yaml import load
import os, sys, shutil, time, datetime, re, filecmp, subprocess, logging, multiprocessing #, hashlib
from Queue import Empty
from optparse import OptionParser
from worker import Worker

"""
A script to traverse a file structure and return the sizes of all the sequences, the number
of files and each range in each folder that is found in the parent directory. Then the total size and total
number of files found is written to a file

Author: Andrew Stevens
"""

class DirectoryListing:
  
  def __init__(self):
    #self.exiting = False
    self.exit = Event()
    self.procs = []

  def stop(self):
    #self.exiting = True
    self.exit.set()
    for proc in self.procs:
      proc.stop()
    print "finished stopping procs"

  def resetExitFlag(self):
    #self.exiting = False
    self.exit.clear()

  ##This method returns the date in a certain format
  def getDate(self):
    return datetime.datetime.now().strftime("%Y-%m-%d") 

  def getDateTime(self):
    return datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y") 

  def get_valid_file(self, dir_listing):
    for file in dir_listing:
      if file.find("128x96") == -1:
        return file

  def get_full_path(self, dir_name, file_name):
    joined_file_name = os.path.join(dir_name, file_name)
    return joined_file_name

  def write_output_to_file(self, save_path, prefix, output):
    #print output
    st = self.getDate()
    system = sys.platform
    if system == 'win32':
      if not save_path == "" and not prefix == "":
        f_path = save_path + "\\" + prefix + "_dir_" + st + ".txt"  ## file name and path of the directory listing file
      elif not save_path == "" and prefix == "":
        f_path = save_path + "\\" + "dir_" + st + ".txt"  ## file name and path of the directory listing file
    else:
      if not save_path == "" and not prefix == "":
        f_path = save_path + "/" + prefix + "_dir_" + st + ".txt"  ## file name and path of the directory listing file
      elif not save_path == "" and prefix == "":
        f_path = save_path + "/" + "dir_" + st + ".txt"  ## file name and path of the directory listing file
    f = open(f_path, "w");
    #print f_path
    for out in output:
      if "Finished writing directory listing" in out:
        break
      else:
        f.write(out)
    f.close()

  #def list_directories(dir_a, save_path="", prefix=""):
  def list_directories(self, dir_a, checkType=''):
    path = ""
    #file_path = ""
    ct = checkType
    ranges = {}
    ranges_list = []
    f_frame = ""  #first frame in sequence
    l_frame = ""  #last frame in sequence
    p_frame = ""  #the previous frame to the one that is being checked
    total_size = 0L  #the total size of the directory
    total_count = 0L ##the total number of files found
    output = []
    received_jobs = []
    #work_queue = multiprocessing.JoinableQueue()   ## queue to hold work for the workers
    work_queue = multiprocessing.Queue()   ## queue to hold work for the workers
    #result_queue = multiprocessing.Queue() ## queue to hold data returned from workers
    result_queue = multiprocessing.JoinableQueue() ## queue to hold data returned from workers
    num_procs = multiprocessing.cpu_count()  ## get the number of processors on the machine
    num_jobs = 0
    date_time = self.getDateTime()
    system = sys.platform
    #t = time.localtime(time.time())
    #st = time.strftime("%Y-%m-%d", t)  #formatting the date to put into the file name of the directory log
    if system == 'darwin':
      path_specified = dir_a.strip("/").split("/")[-1]  ## the parent directory with all the folders, etc in it
    elif system == 'win32':
      path_specified = dir_a.strip("\\").split("\\")[-1]  ## the parent directory with all the folders, etc in it
  
    file_name = "directory_log_" + self.getDate()
    search_sp = re.compile(r"\s[0-9]+$")
    search_un = re.compile(r"_[0-9]+$")
    search_num = re.compile(r"^[0-9]+$")  #regular expression 
    search_mac = re.compile(r"^._")    #regular expression to find any unwanted mac files
    search_mac2 = re.compile(r"^.fs")    #regular expression to find unwanted .fseventsd files
    search_mac_spot = re.compile(r".Spotlight")
    search_mac_apple_dbl = re.compile(r".AppleDouble")  #regular expression to exclude all the apple finder metadata
  
    #regular expression to match the serial number from the output of profiler
    sys_serial = re.compile("(.*?)([\(]{1}[\w]+[\)]{1}):[\s]{1}([\w]+)")
    #frame_num = re.compile("(.*?)([\d]+).([\w]+)")
    div_meg = 1024
    div_gig = 1024.0*1024
    div_tb = 1024.0*1024*1024
    serial_num = ""
    hostname = ""

    ## initial check if we have been cancelled
    if self.exit.is_set():
      return output

    if system == "darwin":
      ##getting the OS, hostname and serial number of the system (we get the serial number only if its a mac)
      hostname = subprocess.Popen(["hostname"], stdout=subprocess.PIPE).communicate()[0]
      p1 = subprocess.Popen(["system_profiler"], stdout=subprocess.PIPE).communicate()[0]
      for out in p1.split("\n"):
        q = sys_serial.match(out)
        if "Serial" in out and q:
          serial_num = q.groups()[-1].strip()
    
    #full_tree = os.walk(dir_a)  #full tree of directories to check
  
    if not self.exit.is_set():
      ## adding jobs to the queue
      for root, dirs, files in os.walk(dir_a, followlinks=True):  #since os.walk returns a tuple, we traverse the tuple and grab the 3 attributes of each directory
        working_dir = root
        path = root    #working directory
        #if not files == [] and not root.split("/")[-1] in dir_check and re.search(search_mac_spot, root)==None and re.search(search_mac_apple_dbl, root)==None:
        if not files == []:
          work_queue.put([root, files, system])
          #work_queue.cancel_join_thread()
          num_jobs += 1
    else:
      ## closing the queues
      result_queue.close()
      work_queue.close()
      #result_queue.join_thread()
      #work_queue.join_thread()
      print "finishing up"
      return output

    if not self.exit.is_set():
      #spawn workers
      for i in range(num_procs):
        worker = Worker(work_queue, result_queue, ct)
        self.procs.append(worker)
        worker.start()
  
      ## add a kill switch for the workers, i.e. 'None'
      for i in range(num_procs):
        work_queue.put(None)
  
    #print "about to join queue"
  
    ## wait for all the jobs to finish
    try:
      result_queue.join()
    except:
      print "unable to join"
    
    #if not self.exiting:
    if not self.exit.is_set():
      #for job in received_jobs:
      for i in range(num_jobs):
        #print "trying to get results from result queue"
        #if self.exiting:
        if self.exit.is_set():
          #print "we get here if we exit while processing stuff"
          ranges = {}
          break
        try:
          ret_job = result_queue.get(timeout=1.0)
          #ret_job = result_queue.get()
          dir_count = ret_job[2]
          dir_size = ret_job[3]
          ranges[ret_job[0]] = ret_job[1]
          total_size += dir_size
          total_count += dir_count
        except Empty:
          #print "Timeout"
          #print "NO MORE JOBS FOUND!!"
          break
        #else:
        #  #print "Canceled!!"
        #  break
    else:
      ranges = {}
 
    # closing queues as this will bring a lot of brain tumours because the program seems stuck even when its not..
    #print "closing queues"
    work_queue.close()
    result_queue.close()

    if not ranges == {}:
      ##Here we go through all the ranges in the dictionary and print them out with their sizes on the same line
      ##writing to file the hostname and the serial number of the machine that did the directory listing
      output.append("Date and time created: %s \n" % date_time)
      output.append("Hostname: " + hostname + "\n")
      if not serial_num == "":
        output.append("Serial Number: " + serial_num + "\n")
      output.append("\n============================================================================================================================\n")
      output.append("\n Directory listing of: " + dir_a +" \n")
      output.append("\n")
      for dir in sorted(ranges.iterkeys()):
        for r in ranges[dir]:
          if not r[0] == "total":
            if system == "win32":
              spec_index = dir.split("\\").index(path_specified)##index of the specified directory in the root path
              if len(str(r[-1]).split(".")[0]) == 0 or len(str(r[-1]).split(".")[0]) < 4:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f B\n" % (r[-2],(r[-1]))
                output.append("\n\t" + "\\".join(dir.split("\\")[spec_index:]) + "\\" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f B\n" % (r[-2],(r[-1])))
              elif len(str(r[-1]).split(".")[0]) == 4 or len(str(r[-1]).split(".")[0]) < 7:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f KB\n" % (r[-2],(r[-1]/div_meg))
                output.append("\n\t" + "\\".join(dir.split("\\")[spec_index:]) + "\\" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f KB\n" % (r[-2],(r[-1]/div_meg)))
              elif len(str(r[-1]).split(".")[0]) == 7 or len(str(r[-1]).split(".")[0]) < 10:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f MB\n" % (r[-2],(r[-1]/div_gig))
                output.append("\n\t" + "\\".join(dir.split("\\")[spec_index:]) + "\\" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f MB\n" % (r[-2],(r[-1]/div_gig)))
              elif len(str(r[-1]).split(".")[0]) == 10 or len(str(r[-1]).split(".")[0]) < 13:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f GB\n" % (r[-2],(r[-1]/div_tb))
                output.append("\n\t" + "/".join(dir.split("\\")[spec_index:]) + "\\" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f GB\n" % (r[-2],(r[-1]/div_tb)))
              elif len(str(r[-1]).split(".")[0]) == 13 or len(str(r[-1]).split(".")[0]) < 16:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f TB\n" % (r[-2],(r[-1]/div_tb))
                output.append("\n\t" + "/".join(dir.split("\\")[spec_index:]) + "\\" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f TB\n" % (r[-2],(r[-1]/div_tb)))
            else:
              spec_index = dir.split("/").index(path_specified)##index of the specified directory in the root path
              if len(str(r[-1]).split(".")[0]) == 0 or len(str(r[-1]).split(".")[0]) < 4:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f B\n" % (r[-2],(r[-1]))
                output.append("\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f B\n" % (r[-2],(r[-1])))
              elif len(str(r[-1]).split(".")[0]) == 4 or len(str(r[-1]).split(".")[0]) < 7:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f KB\n" % (r[-2],(r[-1]/div_meg))
                output.append("\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f KB\n" % (r[-2],(r[-1]/div_meg)))
              elif len(str(r[-1]).split(".")[0]) == 7 or len(str(r[-1]).split(".")[0]) < 10:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f MB\n" % (r[-2],(r[-1]/div_gig))
                output.append("\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f MB\n" % (r[-2],(r[-1]/div_gig)))
              elif len(str(r[-1]).split(".")[0]) == 10 or len(str(r[-1]).split(".")[0]) < 13:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f GB\n" % (r[-2],(r[-1]/div_tb))
                output.append("\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f GB\n" % (r[-2],(r[-1]/div_tb)))
              elif len(str(r[-1]).split(".")[0]) == 13 or len(str(r[-1]).split(".")[0]) < 16:
                #print "\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f TB\n" % (r[-2],(r[-1]/div_tb))
                output.append("\n\t" + "/".join(dir.split("/")[spec_index:]) + "/" + r[0] + " \n\t" + "Total: %d file(s) Size: %0.2f TB\n" % (r[-2],(r[-1]/div_tb)))
            
      if len(str(total_size).split(".")[0]) == 0 or len(str(total_size).split(".")[0]) < 4:
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
        #print "Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f B\n" % (total_count, total_size)
        output.append("Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f B\n" % (total_count, total_size))
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
      elif len(str(total_size).split(".")[0]) == 4 or len(str(total_size).split(".")[0]) < 7:
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
        #print "Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f KB\n" % (total_count, total_size/div_meg)
        output.append("Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f KB\n" % (total_count, total_size/div_meg))
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
      elif len(str(r[0]).split(".")[0]) == 7 or len(str(r[0]).split(".")[0]) < 10:
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
        #print "Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f MB\n" % (total_count, total_size/div_gig)
        output.append("Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f MB\n" % (total_count, total_size/div_gig))
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
      elif len(str(r[0]).split(".")[0]) == 10 or len(str(r[0]).split(".")[0]) < 13:
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
        #print "Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f GB\n" % (total_count, total_size/div_tb)
        output.append("Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f GB\n" % (total_count, total_size/div_tb))
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
      elif len(str(r[0]).split(".")[0]) == 13 or len(str(r[0]).split(".")[0]) < 16:
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
        #print "Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f TB\n" % (total_count, total_size/div_tb)
        output.append("Overall Total:\n\t Number of Files found: %d file(s), Total size: %0.2f TB\n" % (total_count, total_size/div_tb))
        #print "\n=======================================================================\n"
        output.append("\n=======================================================================\n")
            
      #print "======================================================================="
      output.append("=======================================================================\n")
      #print "Finished writing directory listing!"
      output.append("Finished writing directory listing!")
    else:
      output = []
    return output

  def get_dirs(self, path, path_dir):
    jobs = []
    for root, dirs, files in os.walk(path, followlinks=True):  #since os.walk returns a tuple, we traverse the tuple and grab the 3 attributes of each directory
      if not files == []:
        jobs.append(root.split(path_dir)[-1].split("/")[-1])
    return jobs

  """
    Method to get all the jobs for comparing the directories and pushing them to the workers
    path_dir and dest_dir are the lowest level directories in the paths that were supplied by the user
  """
  def check_dirs(self, src, dest, src_dir, dest_dir):
    path = src
    #file_path = ""
    output = []
    received_jobs = []
    work_queue = multiprocessing.Queue()   ## queue to hold work for the workers
    result_queue = multiprocessing.JoinableQueue() ## queue to hold data returned from workers
    num_procs = multiprocessing.cpu_count()  ## get the number of processors on the machine
    num_jobs = 0
    date_time = self.getDateTime()
    system = sys.platform

    src_dirs = self.get_dirs(src, src_dir)
    dest_dirs = self.get_dirs(dest, dest_dir)

    return list(set(src_dirs) - set(dest_dirs))
  
    ## initial check if we have been cancelled
    if self.exit.is_set():
      return output

    if not self.exit.is_set():
      ## adding jobs to the queue
      for root, dirs, files in os.walk(dir_a, followlinks=True):  #since os.walk returns a tuple, we traverse the tuple and grab the 3 attributes of each directory
        working_dir = root
        path = root    #working directory
        #if not files == [] and not root.split("/")[-1] in dir_check and re.search(search_mac_spot, root)==None and re.search(search_mac_apple_dbl, root)==None:
        if not files == []:
          work_queue.put([root, files, system])
          #work_queue.cancel_join_thread()
          num_jobs += 1
    else:
      ## closing the queues
      result_queue.close()
      work_queue.close()
      #result_queue.join_thread()
      #work_queue.join_thread()
      print "finishing up"
      return output

    if not self.exit.is_set():
      #spawn workers
      for i in range(num_procs):
        worker = Worker(work_queue, result_queue, ct)
        self.procs.append(worker)
        worker.start()
  
      ## add a kill switch for the workers, i.e. 'None'
      for i in range(num_procs):
        work_queue.put(None)
  
    #print "about to join queue"
  
    ## wait for all the jobs to finish
    try:
      result_queue.join()
    except:
      print "unable to join"
    
    #if not self.exiting:
    if not self.exit.is_set():
      #for job in received_jobs:
      for i in range(num_jobs):
        #print "trying to get results from result queue"
        #if self.exiting:
        if self.exit.is_set():
          #print "we get here if we exit while processing stuff"
          ranges = {}
          break
        try:
          ret_job = result_queue.get(timeout=1.0)
          #ret_job = result_queue.get()
          dir_count = ret_job[2]
          dir_size = ret_job[3]
          ranges[ret_job[0]] = ret_job[1]
          total_size += dir_size
          total_count += dir_count
        except Empty:
          #print "Timeout"
          #print "NO MORE JOBS FOUND!!"
          break
        #else:
        #  #print "Canceled!!"
        #  break
    else:
      output = []
 
    # closing queues as this will bring a lot of brain tumours because the program seems stuck even when its not..
    #print "closing queues"
    work_queue.close()
    result_queue.close()

    return output
