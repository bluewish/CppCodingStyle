from rules import CSCRuleBase 
import re


class rule_class_variable_low_case_and_end_with_(CSCRuleBase):
    rule_re = re.compile("[a-z_]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "Data members (also called instance variables or member variables) are lower-case with optional underscores like regular variable names, but always end with a trailing underscore."
    
    def category(self):
        return "class_memeber_variable_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        if self.rule_re.match(item_name) == None:
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record) 
        
        if not item_name.endswith("_"):
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record) 
        
        return issue_records
        