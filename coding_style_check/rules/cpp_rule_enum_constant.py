from rules import CSCRuleBase 
import re
import os

class rule_enum_constant_name(CSCRuleBase):
    rule_re = re.compile("[A-Z_]+$")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "The constant value should be capital characters with _"
    
    def category(self):
        return "enum_constant"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        if self.rule_re.match(item_name) == None:
            self._logger.error("Find exception: %s " % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        else:
            print self.rule_re.match(item_name).groups()
            
        if item_name.startswith("_") or item_name.endswith("_"):
            self._logger.error("Find exception: %s " % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
            
        return issue_records