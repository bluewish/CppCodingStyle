import os
import sys
import logging
import locale
import multiprocessing
import rule
import conf
import distutils.file_util
 
import threading 

import dbmgr
    
class CodingStyleCheckerAdapter(object):
    """
    Abstract adpater class for different language.
    """
    def __init__(self, file_name, db, args=None):
        self._filename = file_name
        self._db = db
        self._args = args
        
    @staticmethod
    def get_filter():
        raise NotImplementedError ("This is abstract class, please use inherit class for specific language")
    
    @staticmethod
    def init_rules(rule_file, db):
        raise NotImplementedError ("This is abstract class, please use inherit class for specific language")
    
    def analysis(self):
        # this can be improved also
        if self.db().is_file_expired(self.filename()):
            #self.db().update_file(self.filename())
            self.db().clear_old_issues_of_file(self.filename())
            self.db().update_file_timestamp(self.filename())
            return True
        return False
    
    def filename(self):
        return self._filename
    
    def db(self):
        return self._db
    
    def args(self):
        return self._args
    
    def logger(self):
        return logging.getLogger("Adapter")
    
class CodingStyleChecker:
    
    def __init__(self, rule_filename, conf_filename, adapter_class=CodingStyleCheckerAdapter):
        self._logger = logging.getLogger()
        self._adapter_class = adapter_class
        self._rule = rule.CSCRuleFile(rule_filename) # useless in fact
        self._conf = conf.CSCConfFile(conf_filename)
        self._files = None
        self._db = None
        self._tmp_files = []
        
    def _append_tmpfile(self, file_path_name):
        self._tmp_files.append(file_path_name)
        
    def _remove_tmpfiles(self):
        print "==========remove tmp files:============="
        for file_name in self._tmp_files:
            if os.path.isfile(file_name):
                print "remove tmp file:%s" %(file_name)
                os.remove(file_name)
        
    def execute(self):
        """ checker execute """
        
        # prepare environment
        self._print_environment()
        
        # initialize database
        self._db = dbmgr.CSCDatabase(self._conf.get_database_filepath())
        
        # initialize language rules
        self._adapter_class.init_rules(self._rule, self._db)
        
        # collect all sources from source root path
        self._files = self._collect_source_files()
        
        # setup task pool and semaphore
        self._tasks_semaphore = multiprocessing.Semaphore(self._conf.get_thread_count())
        
        while(True):
            try:
                file_path = self._files.pop()
                self._tasks_semaphore.acquire()
                args = {"includes":self._conf.get_includes(), "macros":self._conf.get_macros()}
                task = CSCWorkerThread(file_path, self._db, self._adapter_class, args, self._task_pre_callback, self._task_post_callback)
                task.start()
            except IndexError:
                break
            
        # Make sure all tasks has been done
        self._print("Wait for all task finished ...")
        for index in range(self._conf.get_thread_count()):
            sys.stdout.write(".")
            self._tasks_semaphore.acquire()
            
        self._print("@@ Finish all tasks ... @@")
        
        self._print("Start to dump result to csv file %s" % self._conf.get_output_csv_path())
        self._db.print_csv(self._conf.get_output_csv_path())
        self._print("\n")
        self._remove_tmpfiles()
        self._print("Done")
        
    def _task_pre_callback(self, file_name):
        self._print("[%s] start analysis ... Zzz " % file_name)
    
    def _task_post_callback(self, file_name):
        self._print("[%s] finish!" % file_name)
        self._tasks_semaphore.release()
        
    def _collect_source_files(self):

        print "collecting sources files ... Zzz"
        file_list = []
        for root, dirs, files in os.walk(self._conf.get_source_root()):
            for dir_item in dirs:
                if dir_item.lower() in self._conf.get_ignore_filters():
                    dirs.remove(dir_item)
                full_dir_name = os.path.realpath(os.path.join(root, dir_item))
                if full_dir_name.lower() in self._conf.get_ignore_paths():
                    dirs.remove(dir_item)
                    
            for file_item in files:
                if file_item.lower() in self._conf.get_ignore_filters():
                    continue
                full_path = os.path.realpath(os.path.join(root, file_item))
                path_items = os.path.splitext(file_item)
                #
                # work around for C++
                #
                if path_items[1].lower() == ".h":
                    hpp_full_path = os.path.join(root, "%s.%s" % (path_items[0], "hpp"))
                    distutils.file_util.copy_file(full_path, hpp_full_path, True, True, True)
                    path_items = (path_items[0], ".hpp")
                    full_path = hpp_full_path
                    self._append_tmpfile(full_path)

                if not path_items[1].lower() in self._adapter_class.get_filter():
                    continue
                
                if full_path.lower() in self._conf.get_ignore_files():
                    continue
                file_list.append(full_path.lower())
                sys.stdout.write(".")
        print "\n"
        print "collecting sources files ... Finished"
        return file_list
    
    def _print_environment(self):
        self._print("===================================================================================")
        self._print("OS type                : %s" % sys.platform)
        self._print("Default encoding       : %s" % sys.getdefaultencoding())
        self._print("Default locale encoding: %s" % locale.getdefaultlocale()[1])
        self._print("File System encoding   : %s" % sys.getfilesystemencoding())
        self._print("Config file            : %s" % os.path.realpath(self._conf.filename()))
        self._print("Rule file              : %s" % os.path.realpath(self._rule.filename()))
        self._print("Sources root path      : %s" % self._conf.get_source_root())
        self._print("Multi-thread counts    : %s" % self._conf.get_thread_count())
        includes = self._conf.get_includes()
        if len(includes) != 0:
            self._print("Include paths          :")
            for item in includes:
                self._print("  %s" % item)
        macro_dict = self._conf.get_macros()
        if macro_dict != None:
            self._print("Macros Definition       :")
            for key in macro_dict.keys():
                if macro_dict[key] != None:
                    self._print("  %-20s = %s" % (key, macro_dict[key]))
                else:
                    self._print("  %-20s" % (key))
        paths = self._conf.get_ignore_paths()
        if len(paths) != 0:
            self._print("Ignore paths            :")
            for path in paths:
                self._print("  %s" % path)
        paths = self._conf.get_ignore_files()
        if len(paths) != 0:
            self._print("Ignore files            :")
            for file_name in paths:
                self._print("  %s" % file_name)
        filters = self._conf.get_ignore_filters()
        if len(filters) != 0:
            self._print("Ignore filters          :")
            for item in filters:
                self._print("  %s" % item)                
        rules = self._rule.get_rules()
        if len(rules) != 0:
            self._print("Rules                   :")
            for index in range(len(rules)):
                self._print("  [%02d] %-20s - %s" % (index, rules[index][0], rules[index][1]))                                  
        self._print("===================================================================================")    
        
    def _print(self, message):
        if hasattr(sys, "frozen"):
            print message
        self._logger.info(message)
            
  
class CSCWorkerThread(threading.Thread):
    def __init__(self, file_name, db, adapter_class, args=None, pre_callback=None, post_callback=None):
        self._file_name = file_name
        self._pre_callback = pre_callback
        self._post_callback = post_callback
        self._args = args
        self._db = db
        self._adapter_class = adapter_class
        threading.Thread.__init__(self)
        
    def run(self):
        if self._pre_callback != None:
            self._pre_callback(self._file_name)
            
        # create adapter instance
        adapter_instance = self._adapter_class(self._file_name, self._db, self._args)
        adapter_instance.analysis()
                
        if self._post_callback != None:
            self._post_callback(self._file_name)
            
        