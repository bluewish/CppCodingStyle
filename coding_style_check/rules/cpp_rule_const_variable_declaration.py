from rules import CSCRuleBase 
import re
import os

class rule_const_variable_declaration(CSCRuleBase):
    rule_re = re.compile("k[A-Z][A-Za-z]+$")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "Use a 'k' followed by mixed case: kDaysInAWeek. This makes it slightly different from other variables"
    
    def category(self):
        return "const_variable_declaration"

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