from rules import CSCRuleBase 
import re
import os

class rule_file_general_rules(CSCRuleBase):
   
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "file general rules"
    
    def category(self):
        return "file"

    # [NOTE] outside should pass in file-name
    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        file_name = ext_param ###########
        try:
            fd = open(file_name, "r")
            lines = fd.readlines()
            fd.close()
            for index in range(len(lines)):
                if len(lines[index]) > 80:
                    #self.db().report_issue(file_name, index, 0, "line should not exceed 80 characters", lines[index])
                    issue_record = (index, 0, "line should not exceed 80 characters", lines[index], CSCRuleBase.rule_errorlevel_low, "") 
                    issue_records.append(issue_record)
                column = lines[index].find("\t")
                if column != -1:
                    self._logger.error("Find exception: (%d:%d) " % (index, column))
                    #self.db().report_issue(file_name, index, column, "should not use tab character", file_name)
                    issue_record = (index, column, "should not use tab character", file_name, CSCRuleBase.rule_errorlevel_low, "") 
                    issue_records.append(issue_record)
        except:
            pass
        
        return issue_records