
import os
import sys
import sqlite3
import datetime
import logging
import threading

from rules import CSCRuleBase

def convert_for_csv_field_str(field_str):
    field_str = field_str.strip()
    if field_str.find(',') >=0 or field_str.find('"') >=0 or field_str.find('\n') >=0:
        new_str = field_str
        new_str = new_str.replace('"','""') 
        #new_str = new_str.replace(',','","')
        #new_str = new_str.replace('\n','"\n"')
        #new_str = new_str.replace('"','""') 
        new_str = '"' + new_str + '"'
        return new_str
    else:
        return field_str
        

class CSCDatabase:
    
    def __init__(self, db_file, recreate=False):
        self._logger = logging.getLogger("Database")
        self._db_filename = db_file
        self._file_timestamps = {}
        self._updated_files = []
        self._added_files = []
        self._lock = threading.Lock()
        
        if not os.path.exists(db_file) or recreate:
            self._create()
            
        self._read_all_file_timestamp_from_db()
        
    def __del__(self):
        self._update_file_timestamps_to_db()
        
    def _create(self):
        self._logger.info("Creating database file %s due to missing..." % self._db_filename)
        if os.path.exists(self._db_filename):
            os.remove(self._db_filename)
            
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.executescript("""
            create table files (
                filename text,
                last_update timestamp
            );
            create table issues (
                filename text,
                line_row integer,
                line_column integer,
                rule_name text,
                source text,
                errorlevel integer,
                description text
            );
            """)
        con.commit()
        cur.close()
        con.close()
    
    # all file time stamp can be read at a time, then buffer in memory, it can reduce read-count to db and improve speed   
    def is_file_expired_depreted(self, file):
        assert(os.path.exists(file))
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("select last_update from files where filename=?", (file,))
        row = cur.fetchone()
        
        if row == None:
            cur.close()
            return True
        else:
            old_timestamp = row[0]
            cur_timestamp = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
            if old_timestamp < cur_timestamp:
                self._logger.info("file %s is modified after last scan", file)
                cur.close()
                return True
            
        cur.close()
        con.close()
        return False
    
    def is_file_expired(self, file):
        assert(os.path.exists(file))
        self._lock.acquire()
        result = False
        if not self._file_timestamps.has_key(file):
            result = True
        else:
            old_timestamp = self._file_timestamps[file]
            cur_timestamp = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
            if old_timestamp < cur_timestamp:
                self._logger.info("file %s is modified after last scan", file)
                result = True
            else:
                result = False
        self._lock.release()
        return result
    
    def clear_old_issues_of_file(self, file_name):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("delete from issues where filename=?", (file_name,))
        con.commit()
        cur.close()
        con.close()
        
    def _read_all_file_timestamp_from_db(self):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("select filename, last_update from files")
        
        self._lock.acquire()
        for row in cur:
            filename = row[0]
            timestamp = row[1]
            self._file_timestamps[filename] = timestamp
        self._lock.release()
        
        cur.close()
        con.close()
            
    def _update_file_timestamps_to_db(self):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        
        self._lock.acquire()
        for file_name in self._updated_files:
            time_stamp = self._file_timestamps[file_name]
            cur.execute("update files set last_update=? where filename=?", (time_stamp, file_name))
        for file_name in self._added_files:
            time_stamp = self._file_timestamps[file_name]
            cur.execute("insert into files(filename, last_update) values (?, ?)", (file_name, time_stamp))
        self._updated_files = []
        self._added_files = []
        self._lock.release()
        
        con.commit()
        cur.close()
        con.close()
        
        
    def update_file_depreted(self, file):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("select last_update from files where filename=?", (file,))
        row = cur.fetchone()
        file_cur_time = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
        if row == None:
            cur.execute("insert into files(filename, last_update) values (?, ?)", (file, file_cur_time))
        else:
            cur.execute("update files set last_update=? where filename=?", (file_cur_time, file))
            
        con.commit()
        cur.close()
        con.close()
        
    def update_file_timestamp(self, file):
        file_cur_time = datetime.datetime.fromtimestamp(os.stat(file).st_mtime)
        self._lock.acquire()
        if self._file_timestamps.has_key(file):
            self._updated_files.append(file)
        else:
            self._added_files.append(file)
        self._file_timestamps[file] = file_cur_time
        self._lock.release()
        
    def report_issue(self, file_name, column, row, rule, source = None, 
                     errorlevel = CSCRuleBase.rule_errorlevel_warning,
                     description = None):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("insert into issues(filename, line_row, line_column, rule_name, source, errorlevel, description) values (?, ?, ?, ?, ?, ?, ?)", 
                    (file_name, column, row, rule, source, errorlevel, description))
        con.commit()
        cur.close()
        con.close()
        
    def report_issues(self, file_name, issue_items_for_same_file):
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        #(line, column, rule, source, errorlevel, description)
        for (row, column, rule, source, errorlevel, description) in issue_items_for_same_file:
            cur.execute("insert into issues(filename, line_row, line_column, rule_name, source, errorlevel, description) values (?, ?, ?, ?, ?, ?, ?)", 
                    (file_name, row, column, rule, source, errorlevel, description))
        con.commit()
        cur.close()
        con.close()
        
    def print_csv(self, csv_file_name):
        try:
            fd = open(csv_file_name, "w")
        except:
            raise Exception("Fail to open output csv file %s for writting." % csv_file_name)
        
        self._update_file_timestamps_to_db()  ######
        
        fd.write("filename, line_row, line_column, rule_name, source, errorlevel, description\n" ) 
        con = sqlite3.connect(self._db_filename, detect_types=sqlite3.PARSE_DECLTYPES)
        cur = con.cursor()
        cur.execute("select filename, line_row, line_column, rule_name, source, errorlevel, description from issues")
        row = cur.fetchall()
        for item in row:
            #sys.stdout.write(".")
            filename = convert_for_csv_field_str(item[0])
            rulename = convert_for_csv_field_str(item[3])
            source = convert_for_csv_field_str(item[4])
            description = convert_for_csv_field_str(item[6])
            fd.write("%s, %d, %d, %s, %s, %d, %s\n" % (filename, item[1], item[2], rulename, source, item[5], description ))
        fd.close()
        cur.close()
        con.close()
        
if __name__ == "__main__":
    db_obj = CSCDatabase("d:\\temp.db", False)
    if db_obj.is_file_expired("d:\\test.txt"):
        db_obj.update_file("d:\\test.txt")
        db_obj.report_issue("d:\\test.txt", 2, 2, "haha", "hoho")
        db_obj.report_issue("d:\\test.txt", 2, 2, "haha", "hoho")
        