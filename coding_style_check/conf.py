import os
import ConfigParser

class CSCConfigFileException(Exception):
    def __init__(self, filename, message):
        self._filename = os.path.realpath(filename)
        self._message  = message
        Exception.__init__(self, message)
        
    def __str__(self):
        return "Config file Error: %s [%s]" % (self._message, self._filename)
    
class CSCConfFile:
    """
    The setting file, see the template at below of this file.
    """
    
    def __init__(self, filename):
        self._filename = filename
        
        if not os.path.exists(self._filename):
            raise Exception("Fail to find the conf file %s" % self._filename)
        
        self._config = ConfigParser.ConfigParser(allow_no_value=True)
        self._config.optionxform = str
        self._config.read(self._filename)

        self._validate()
        self._remove_database_file()
        
    def filename(self):
        """ return the file name """
        return self._filename
           
    def get(self, name, default, section="global"):
        """
        get a setting from configure file. If setting does not exist, then create
        by given default value. 
        """
        dirty = False
        if not self._config.has_section(section):
            self._config.add_section(section)
            dirty = True
        
        if not self._config.has_option(section, name):
            self._config.set(section, name, default)
            dirty = True
        
        if default != None and self._config.get(section, name, default) == None:
            self._config.set(section, name, default)
            dirty = True
        
        if dirty:
            self._config.write(open(self._filename, "w"))
            
        return self._config.get(section, name, default)
            
    def get_includes(self):
        """ return the list of include path """
        ret = []
        if not self._config.has_option("global", "includes"):
            return ret
        
        value = self._config.get("global", "includes")
        
        for item in value.split(";"):
            item = item.strip()
            if len(item) == 0:
                continue
            ret.append(item.strip())
        return ret
    
    def get_source_root(self):
        """ get the path of source code root directory """
        if not self._config.has_option("global", "source_root"):
            raise CSCConfigFileException(self._filename, 
                                         "Miss source_root at global section.")
        
        source_root = self.get("source_root", None)
        if not os.path.exists(source_root):
            raise CSCConfigFileException(self._filename, 
                                         "The source dir path %s does not exist." % source_root)
        
        return source_root
            
    def get_thread_count(self):
        """ get thread count , by default is 4 """
        return int(self.get("threads", 4))
    
    def get_macros(self):
        """ get macro list, only for c/c++ language """
        macro_dict = {}
        if not self._config.has_section("macros"):
            return None
        
        macro_keys = self._config.options("macros")
        for macro_key in macro_keys:
            macro_dict[macro_key] = self._config.get("macros", macro_key, None) 
        return macro_dict
    
    def get_database_filepath(self):
        """ return database file path specified in conf file as database_path """
        if not self._config.has_option("global", "database_path"):
            raise CSCConfigFileException(self._filename, 
                                         "Miss database_path at global section.")
        return os.path.realpath(self._config.get("global", "database_path"))
    
    def get_output_csv_path(self):
        """ return result csv file path specified in conf file as output_csv_path """
        if not self._config.has_option("global", "output_csv_path"):
            raise CSCConfigFileException(self._filename, 
                                         "Miss output_csv_path at global section.")
        return os.path.realpath(self._config.get("global", "output_csv_path"))
    
    def get_ignore_filters(self):
        """ get ignore filtes specified in conf file as ignore_filters """
        ignore_filters = self._config.get("global", "ignore_filters", None)
        if ignore_filters == None or len(ignore_filters) == 0:
            return []
        ret = ignore_filters.split(";")
        ret = [item.strip().lower() for item in ret]
        return ret
                
    def get_ignore_paths(self):
        """ 
        return ignore path list specified in conf file as ignore_paths 
        Each path has been converted to absolute path.
        """
        ignore_paths = self._config.get("global", "ignore_paths", None)
        if ignore_paths == None or len(ignore_paths) == 0:
            return []
        
        ret = []
        for path in ignore_paths.split(";"):
            path = path.strip()
            if os.path.exists(path):
                ret.append(os.path.realpath(path).lower())
            elif os.path.exists(os.path.join(self.get_source_root(), path)):
                ret.append(os.path.realpath(os.path.join(self.get_source_root(), path)).lower())
                os.path.realpath(os.path.join(self.get_source_root(), path)).lower()
        return ret
    
    def get_ignore_files(self):
        """ 
        return ignore file list specified in conf file as ignore_files 
        Each path has been converted to absolute path.
        """        
        ignore_files = self._config.get("global", "ignore_files", None)
        if ignore_files == None or len(ignore_files) == 0:
            return []
        
        ret = []
        for path in ignore_files.split(";"):
            path = path.strip()
            if os.path.exists(path):
                ret.append(os.path.realpath(path).lower())
            elif os.path.exists(os.path.join(self.get_source_root(), path)):
                ret.append(os.path.realpath(os.path.join(self.get_source_root(), path)).lower())
                os.path.realpath(os.path.join(self.get_source_root(), path)).lower()
            else:
                raise CSCConfigFileException(self._filename, 
                                             "Invalid path %s for ignore_paths" % path)
        return ret
        
    def _validate(self):
        count = self.get_thread_count()
        if count < 0 or count > 16:
            raise CSCConfigFileException(self._filename, 
                                         "The valid range for thread count is 0 ~ 16")
        
        for path in self.get_includes():
            if not os.path.exists(path):
                raise CSCConfigFileException(self._filename, 
                                             "The include path %s does not exist." % path)
            
        self.get_source_root()
        self.get_output_csv_path()
     
    def _remove_database_file(self):
        """
        remove database file if configure file is changed
        """
        if os.path.exists(self.get_database_filepath()):
            _conftime = os.path.getmtime(self.filename())
            _dbtime = os.path.getmtime(self.get_database_filepath())
            if _conftime > _dbtime:
                os.remove(self.get_database_filepath())  
        
"""
# This is a template of setting file for coding style checker

##
## global section for general settings:
##
[global]

#
# threads : the count of multi-threads, range (0 ~ 16)
#
threads = 8

#
# includes : the include path when compiling the source
#            the paths are seperated by ;
#  
includes = E:\myworks\lir\include;
           E:\myworks\lir\local_identity_registration\local_identity_registration\src;
           E:\research\boost_1_46_1;
           E:\myworks\lir\local_identity_registration\3rd-party\json\include;
           E:\myworks\lir\local_identity_registration\3rd-party\openssl\include;
           E:\myworks\lir\local_identity_registration\3rd-party\sqlite3\include

#
# source_root : the root directory for source code, all source under this directory will be scan and compiled
#
source_root = E:\myworks\lir\local_identity_registration\local_identity_registration\src\cmpc\lir\

#
# database_path : the path for cached database file
#
database_path = e:\my_test.db

#
# output_csv_path : the csv file path for reporting final result
#
output_csv_path = e:\result.csv

#
# ignore_filters: the filter string list seperated by ;
#                 if file or path contains one filter string, then ignore
#
ignore_filters = .svn;_svn;.git

#
# ignore_paths : the path list for ignore, seperated by ;
#                could be absolute path or relative path related to source_root
#
ignore_paths = key_generation;
               E:\myworks\lir\local_identity_registration\local_identity_registration\src\cmpc\lir\service

#
# ignore_files : the file list for ignore, seperated by ;
#                could be absolute path or relative path related to source_root                
#
ignore_files = E:\myworks\lir\local_identity_registration\local_identity_registration\src\cmpc\lir\runtime\windows\LIRService_p.c


##
## macros section to define all macros used in compiling sources
##
[macros]
CMPC_IMP=
_WIN32
CMPC_Status=int
DCSSTUBIMP=

"""        