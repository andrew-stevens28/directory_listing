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
  def list_directories(self, dir_a):
    path = ""
    #file_path = ""
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
          #(ranges_list, dir_count, dir_size) = get_listings(root, files, system)
          #print "========================================================================================"
          #print root
          #print dirs
          #print files
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

    #print work_queue
  
    if not self.exit.is_set():
      #spawn workers
      for i in range(num_procs):
        worker = Worker(work_queue, result_queue)
        self.procs.append(worker)
        worker.start()
  
      ## add a kill switch for the workers, i.e. 'None'
      for i in range(num_procs):
        work_queue.put(None)
  
    #print "about to join queue"
  
    #if not self.exit.is_set():
    ## wait for all the jobs to finish
    #print "joining result queue"
    try:
      result_queue.join()
    except:
      print "unable to join"
    #print "finished joining!!"
    #for p in procs:
    #  p.join()
  
    #print "queue has joined, now processing data..."
    
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
 
    #print ranges
    #print "length of ranges: %d" % len(ranges)
    # closing queues as this will bring a lot of brain tumours because the program seems stuck even when its not..
    #print "closing queues"
    work_queue.close()
    result_queue.close()
    #print ranges
    ##now we start writing to the file
  
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


  """
    Method to grab all the directories of a copied folder
  """
  def get_dirs(root, job_name):
    #dir_dict = {}
    dir_list = []
    full_tree = os.walk(root)
    dir_check = ["128x96"]          ##directories to not include
    has_files = 0
    
    for root, dirs, files in full_tree:
      #if not dirs == [] and not root.split("/")[-1] in dir_check:
        #if not files == []:
        #  has_files = 1
        ## change the root string to have the job_name as the root so we can check to see which directories are missing
        ##must have the job_name or this doesnt work!!
      #print "/".join(root.split("/")[root.split("/").index(job_name):])
      #dir_dict["/".join(root.split("/")[root.split("/").index(job_name):])] = [dirs, has_files]
    ##Here we add the directory to the list since we dont care if there are files or not because we are just checkinf directories right now
      if system == "win32":
        dir_list.append("\\".join(root.split("\\")[root.split("\\").index(job_name):]))
      else:
        dir_list.append("/".join(root.split("/")[root.split("/").index(job_name):]))
      #has_files = 0
    return dir_list

  """
    Method to check if all the directories are the same
  """
  def check_dirs(self, src, dest, job_name):
    #src_dict = get_dirs(src, job_name)    ##getting dictionary of all the directories in the source directory
    src_list = self.get_dirs(src, job_name)    ##getting list of all the directories in the source directory
    #dest_dict = get_dirs(dest, job_name)    ##getting dictionary of all the directories in the destination directory
    dest_list = self.get_dirs(dest, job_name)    ##getting list of all the directories in the destination directory
    output = []                  ## list to hold the output so we can send it back to the gui to display
    count = 0
    testing_list = []
    #sorted_src_keys = sorted(src_dict.iterkeys())
    sorted_src_keys = sorted(src_list)    ## sorting the list of directories although these are not keys anymore, just for ease sake I left it
    #sorted_dest_keys = sorted(dest_dict.iterkeys())
    sorted_dest_keys = sorted(dest_list)    ##sorting the list of directories
    if len(sorted_src_keys) > len(sorted_dest_keys):
      #for src_key in sorted_src_keys:
      #  for dest_key in sorted_dest_keys:
      result_set = set(sorted_src_keys) - set(sorted_dest_keys)    ## get the result of minusing the sets
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "\t There are folders missing from the Destination directory: "
      output.append("\t There are folders missing from the Destination directory: ")
      for dir in list(result_set):          ##printing out the directories that are missing
        output.append(dir + "\n")
        #print dir
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "there are less files in the destination than in the source"
      count += 1
    elif len(sorted_src_keys) < len(sorted_dest_keys):      ##this is the reverse of the above just incase the directories were reversed
      result_set = set(sorted_dest_keys) - set(sorted_src_keys)
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "\t There are folders missing from the Source directory: "
      output.append("\t There are folders missing from the Source directory: ")
      for dir in list(result_set):
        #print dir
        output.append(dir + "\n")
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #for src_key in sorted_src_keys:
      #  for dest_key in sorted_dest_keys:
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "\t There are folders missing from the Source directory, please check the directories... "
      output.append("\t There are folders missing from the Source directory, please check the directories... ")
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      count += 1
      #print "there are less files in the src directory than the desination directory"
    #print output
    return (count, output)
      
  """
    Method to grab all the directories for a given folder
  """
  def get_files(self, root):
    ##get the directories of specified folder
    search_mac = re.compile(r"^._")    #regular expression to find any unwanted mac files
    search_ds_store = re.compile(r".DS_Store")
    search_mac2 = re.compile(r"^.fs")    #regular expression to find unwanted .fseventsd files
    resolution = re.compile(r"[0-9][0-9][0-9][0-9]x[0-9][0-9][0-9][0-9]")
    none_detected = 0
    no_files = 0
    no_files_in_dir = 0
    total_dirs = 0
    dir_dict = {}            ##dictionary to hold all the directories and the files
    files_to_add = []
    full_tree = os.walk(root)
    dir_check = ["128x96"]          ##directories to not include
    output = []
    no_files_found = 0
    
    for root, dirs, files in full_tree:      ##traversing full tree to get files to return
      working_dir = root
      no_files_in_dir = 0
      if system == "win32":
        check_working = working_dir.split("\\")[-1]
      else:
        check_working = working_dir.split("/")[-1]
      if not files == [] and not check_working in dir_check:  ##checking that we actually have files to check
        for file in files:            ## traversing files found in the directory listing
          if re.search(search_mac, file)==None and re.search(search_mac2, file)==None and re.search(search_ds_store, file)==None:  ##checking to see if we have any mac files that we need to ignore
            files_to_add.append(file)
        if not files_to_add==[]:    ##checking that we actually found files
          dir_dict[root] = files_to_add
      else:
        no_files += 1
        no_files_in_dir +=1
      files_to_add=[]
      total_dirs += 1
      if no_files_in_dir>0 and not re.search(resolution, root.split("/")[-1])==None:
        output.append("\n===========================================================================================\n")
        #print "\n===========================================================================================\n"
        output.append("The directory: " + root + ", had no files in it!")
        #print "The directory: " + root + ", had no files in it!"
        #print "\n===========================================================================================\n"
        output.append("\n===========================================================================================\n")
        none_detected = 1
    if no_files==total_dirs:
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "There were no files found in the folder:" + root + "! Check that there are files in the folders and try again..."
      output.append("There were no files found in the folder:" + root + "! Check that there are files in the folders and try again...")
      #print "Exiting..."
      output.append("Stopping directory check...")
      output.append("\n===========================================================================================\n")
      #print "\n===========================================================================================\n"
      #sys.exit(1)
      no_files_found = 1
      return (dir_dict, none_detected, no_files_found, output)
    else:
      return (dir_dict, none_detected, no_files_found, output)

  """
  This method is used to compare two directories and see if the files are the same
  """
  def compare_dir(self, src, dir, job_name):
    output = []      ##list to hold the output picked up from the directory comparison
    dir_detect = -1
    src_detect = -1
    count = -1      ## a count to check the number of files that are different
    if dir == src:    ###checking to see if the source directory is the same as the 
      #print "source directory is the same as the compare directory, enter the directory where the files were copied to"
      output.append("""
      ERROR: source directory is the same as the compare directory, enter the directory where the files were 
      copied from in the 'Select Source Directory' field
              """)
      #print output
      return (count, dir_detect, src_detect, output)
      
    
    (dir_dict, dir_detect, dir_nothing_found, dir_output) = self.get_files(dir)  ##destination dictionary of files grabs only directories that have files in them
    #print src_dict
    (src_dict, src_detect, src_nothing_found, src_output) = self.get_files(src)  ## compare dictionary with files to compare to source
    #print comp_dict
    if dir_nothing_found > 0 and src_nothing_found>0:
      output.extend(dir_output)
      output.extend(src_output)
      return (count, dir_detect, src_detect, output)
    elif dir_nothing_found >0 and src_nothing_found ==0:
      output.extend(dir_output)
      return (count, dir_detect, src_detect, output)
    elif dir_nothing_found == 0 and src_nothing_found >0:
      output.extend(src_output)
      return (count, dir_detect, src_detect, output)
      
    #print src_dict
    #print "============================================================================"
    #print dir_dict
    test_list = []
    src_list_rem = []
    dir_list_rem = []
    src_keys_list = list(src_dict.iterkeys())
    dir_keys_list = list(dir_dict.iterkeys())
    dir_detect = 0
    src_detect = 0
    count = 0
    
    ###zipping the directories up was not working as there were separate files sometimes
    ## so instead we check the keys list of the dictionary which we setup as the root of the folder
    if len(dir_keys_list) > len(src_keys_list):
      #print "src_dict iterkeys length: " + str(len(list(src_dict.iterkeys())))
      #print "comp_dict iterkeys length: " + str(len(list(comp_dict.iterkeys())))
      for dir_key in sorted(dir_dict.iterkeys()):
        for src_key in sorted(src_dict.iterkeys()):
          if system == "win32":
            if "\\".join(dir_key.split("\\")[dir_key.split("\\").index(job_name):]) == "\\".join(src_key.split("\\")[src_key.split("\\").index(job_name):]):
              dir_list_rem.append(dir_key)
          else:
            if "\\".join(dir_key.split("\\")[dir_key.split("\\").index(job_name):]) == "\\".join(src_key.split("\\")[src_key.split("\\").index(job_name):]):
              dir_list_rem.append(dir_key)
      result_set = set(dir_keys_list) - set(dir_list_rem)
      if not result_set == set([]):
        #print "There are files and folders missing from the destination directory: "
        output.append("There are files and folders missing from the Source directory: \n")
        ##looping through the result set that we found were not copied across to the destination directory
        for dir_key_set in result_set:
          ##creating the output string to send back to gui and print out
          output_str = "The directory: " + dir_key_set + ", with files: \n"
          #print "The directory: " + src_key + ", with files: "
          for file in dir_dict[dir_key_set]:
            #print file
            output_str += file + "\n"
          output.append(output_str)
          #print src_dict[src_key]
      #print "There are directories of files missing from the desination directory: "
      
      count +=1
      ##case where the directories in the comparing directory is greater than the source, this could be due to the source and destination directory were swapped at invocation
    if len(dir_keys_list) < len(src_keys_list):
      for src_key in sorted(src_dict.iterkeys()):
        for dir_key in sorted(dir_dict.iterkeys()):
          if system == "win32":
            if "\\".join(src_key.split("\\")[src_key.split("\\").index(job_name):]) == "\\".join(dir_key.split("\\")[dir_key.split("\\").index(job_name):]):
              src_list_rem.append(src_key)
          else:
            if "/".join(src_key.split("/")[src_key.split("/").index(job_name):]) == "/".join(dir_key.split("/")[dir_key.split("/").index(job_name):]):
              src_list_rem.append(src_key)
      result_set = set(src_keys_list) - set(src_list_rem)
      if not result_set == set([]):
        #print "There are files and folders missing from the Source directory: "
        output.append("There are files and folders missing from the Destination directory: \n")
        for src_key_set in result_set:
          output_str = "The directory: " + src_key_set + ", with files: \n"
          #print "The directory: " + src_key + ", with files: "
          #output.append()
          for file in src_dict[src_key_set]:
            #print file
            output_str += file + "\n"
          output.append(output_str)
          #print src_dict[src_key]
      #print "There are directories of files missing from the desination directory: "
      
      count +=1
  
    ##base case when the directories have been copied over correctly
    if len(dir_keys_list) == len(src_keys_list):
      for dir_key, src_key in zip(sorted(dir_keys_list), sorted(src_keys_list)):
        if set(dir_dict[dir_key]) > set(src_dict[src_key]):    ###here we are checking to see if there are less files in the destination directory
          #print "==========================================================================================="
          output.append("===========================================================================================")
          #print "There are files missing from the desintation directory: " + dir_key + "\n"
          output.append("There are files missing from the Source directory: " + src_key + "\n")
          missing_files = set(dir_dict[dir_key]) - set(src_dict[src_key])
          #print "These Files are: \n"
          output.append("These Files are: \n")
          output_str = ""
          for file in sorted(missing_files):
            #print file + "\n"
            output_str += file + "\n"
          output.append(output_str)
          #print "==========================================================================================="
          output.append("===========================================================================================")
          count += 1
        elif set(dir_dict[dir_key]) < set(src_dict[src_key]):    ###here we are checking to see if there are more files in the destination, shouldnt ever get here though...
          #print "==========================================================================================="
          output.append("===========================================================================================")
          #print "There are extra files in the Source directory: "+ src_key +"\n"
          output.append("There are extra files in the Destination directory: "+ dir_key +"\n")
          extra_files = set(src_dict[src_key]) - set(dir_dict[dir_key])
          output_str = ""
          #print "These files are: \n"
          output.append("These files are: \n")
          for file in sorted(extra_files):
            #print file + "\n"
            output_str += file + "\n"
          output.append(output_str)
          #print "==========================================================================================="
          output.append("===========================================================================================")
          count += 1
        else:                ##we get here if there are the same number of files in both directories
          #print "There should be equal files in the directories"
          diff_files = []
          for dir_file, src_file in zip(sorted(dir_dict[dir_key]), sorted(src_dict[src_key])):
            result = filecmp.cmp(self.get_full_path(dir_key, dir_file), self.get_full_path(src_key, src_file))    ##getting result of compare
            #print result
            if not result:
              diff_files.append(self.get_full_path(src_key, src_file) + "," + self.get_full_path(dir_key, dir_file))    ##appending files that differ from the original files
              count += 1
          if not diff_files==[]:
            #print "\n===========================================================================================\n"
            output.append("\n===========================================================================================\n")
            output_str = ""
            for file in diff_files:
              #print "The file: " + file.split(",")[0] + ", is different from the source: " + file.split(",")[-1]
              output_str += "The file: " + file.split(",")[0] + ", is different from the copied file: " + file.split(",")[-1] + "\n\n"
            #print "\n===========================================================================================\n"
            output.append(output_str)
            output.append("\n===========================================================================================\n")
      #print count
      #print dir_detect
      #print src_detect
        #print output
        return (count, dir_detect, src_detect, output)

  """
  Method to create a file with all the checksum strings for a list of frames requested by the user
  """
  def create_checksum(self, root_dir):
    if system == "win32":
      checksum_file = root_dir + "\\md5sum.txt"
    else:
      checksum_file = root_dir + "/md5sum.txt"
    output = []
    no_files = 0
    file = open(checksum_file, 'a')
    (files_dict, none_detected, no_files, output) = self.get_files(root_dir)
    if no_files>0 or none_detected>0:
      output.append("\n===========================================================================================\n")
      output.append("There were no files found in the directory, please check the directories and try again...")
      output.append("\n===========================================================================================\n")
    else:
      for dir in sorted(files_dict.iterkeys()):
        for f in files_dict[dir]:
          if system == "win32":
            out_file = dir + "\\" + f
          else:
            out_file = dir + "/" + f
          #file.write(md5_checksum(dir + "/" + f) + " " + dir + "/" + f + "\n")
          p1 = subprocess(["md5", "-r", out_file], stdout=subprocess.PIPE)
          output = p1.communicate()[0]
          file.write(output + " " + out_file + "\n")
          p1.stdout.close()
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
      #print "Finished writing md5 checksum file!!!"
      output.append("Finished writing md5 checksum file!!!")
      #print "\n===========================================================================================\n"
      output.append("\n===========================================================================================\n")
    return output

"""
# test method for multiprocessing
def f(x):
  return x*x

if __name__ == '__main__':
  log_to_stderr(logging.DEBUG)
  cores = cpu_count()
  print "number of CPUs/Cores on this machine is:", cores
  pool = Pool(processes=cores)
  result = pool.apply_async(f, [10])
  print result.get(timeout=1)
  print pool.map(f, range(10))
  parser = OptionParser()
  parser.add_option("-d", "--directory", dest="directory", help="list the contents of a directory", metavar="DIR")
  (options, args) = parser.parse_args()
  directory = options.directory
  list_directories(directory)
  list_directories()
"""
