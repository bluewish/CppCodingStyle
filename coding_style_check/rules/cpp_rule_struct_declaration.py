from rules import CSCRuleBase 
import re
import os

class rule_struct_declaration_name(CSCRuleBase):
    rule_re = re.compile("([A-Z]+_)?([A-Z][a-zA-Z]+)(_S)?$")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "The suffix '_E' or '_S' is also used in the typedef of an enum or struct"
    
    def category(self):
        return "struct_declaration"

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