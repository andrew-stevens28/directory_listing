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
    while not self.exit.is_set():
      #get a task
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

  """
    Method to grab all the directories for a given folder
  """
  def get_files(self, root):
    ##get the directories of specified folder
    search_mac = re.compile(r"^._")    #regular expression to find any unwanted mac files
    search_ds_store = re.compile(r".DS_Store")
    search_mac2 = re.compile(r"^.fs")    #regular expression to find unwanted .fseventsd files
    resolution = re.compile(r"[0-9][0-9][0-9][0-9]x[0-9][0-9][0-9][0-9]")
    system = sys.platform
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
  def compare_dir(self, src, dest):
    output = []      ##list to hold the output picked up from the directory comparison
    dir_detect = -1
    src_detect = -1
    count = -1      ## a count to check the number of files that are different
    system = sys.platform

    print "src path: " + src
    print "dest path: " + dest
    
    (dir_dict, dir_detect, dir_nothing_found, dir_output) = self.get_files(dest)  ##destination dictionary of files grabs only directories that have files in them
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

