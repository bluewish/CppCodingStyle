from rules import CSCRuleBase 
import re

class rule_call_no_space_before_after_parentheses(CSCRuleBase):
    rule_re = re.compile("[A-Z][a-z]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "There should no space before/after parenthese when call function."
    
    def category(self):
        return "call_function"

    def execute(self, item_name, line, column, source, ext_param):
        c_left = source.find("(")
        issue_records = []
        if c_left != -1:
            if source[c_left - 1] == " " or source[c_left + 1] == " ":
                self._logger.error("Find exception: (%d) " % c_left)
                #self.db().report_issue(file_name, line, c_left, self.name(), source)  
                issue_record = (line, c_left, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record)             

        c_right = source.find(")")
        if c_right != -1:
            if source[c_right - 1] == " ":
                self._logger.error("Find exception: (%d) " % c_right)
                #self.db().report_issue(file_name, line, c_right, self.name(), source) 
                issue_record = (line, c_right, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                issue_records.append(issue_record)                
                
        return issue_records