from rules import CSCRuleBase 
#import re
import os

class rule_param_declaration_8_space_indent(CSCRuleBase):
    #rule_re = re.compile("([ \t]+)\w+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "There should be 8 space indent for param declaration in seperate line."
    
    def category(self):
        return "param_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        (parent_start_ln, parent_start_end) = ext_param
        if parent_start_ln == line:
            return []
        if (column - parent_start_end) != 8:
            self._logger.error("Find exception: %s" % source)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records