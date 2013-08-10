from rules import CSCRuleBase 
import re

class rule_1_space_before_after_binary_operator(CSCRuleBase):
    rule_re = re.compile("([ \t]+)[!=-><&*+/]+([ \t]+)")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "There should at least 1 space before/after binary operator."
    
    def category(self):
        return "binary_operator"

    def execute(self, item_name, line, column, source, ext_param):
        m = self.rule_re.search(source)
        issue_records = []
        if m == None:
            self._logger.error("Find exception: (%d:%d) " % (line, column))
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records