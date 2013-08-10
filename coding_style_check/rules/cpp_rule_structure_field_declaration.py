from rules import CSCRuleBase 
import re


class rule_struct_field_should_small(CSCRuleBase):
    rule_re = re.compile("[a-z_]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "Data members in structs should be named like regular variables without the trailing underscores that data members in classes have"
    
    def category(self):
        return "struct_field_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        if self.rule_re.match(item_name) == None:
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        
        if item_name.endswith("_"):
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        
        return issue_records
        