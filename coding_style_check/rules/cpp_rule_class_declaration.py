from rules import CSCRuleBase 
import re

class rule_class_decalaration_pascal_case(CSCRuleBase):
    rule_re = re.compile("[A-Z][a-z]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "The class declaration should be in PascalCase."
    
    def category(self):
        return "class_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        if self.rule_re.match(item_name) == None:
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records
        
class rule_class_decalaration_no_mfc_prefix(CSCRuleBase):
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "Unless a class is derived from MFC, the MFC prefix 'C' or 'I' should not be used."
    
    def category(self):
        return "class_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        if item_name[0] in ["C", "I"]:
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records        