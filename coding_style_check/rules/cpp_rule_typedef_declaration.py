from rules import CSCRuleBase 
import re


class rule_typedef_declaration(CSCRuleBase):
    rule_re = re.compile("[A-Z][a-zA-Z]+$")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return """"
        Type names should be in PascalCase. Classes, structs, typedefs, and enums 
        are all the same. They start with a capital letter and have a capital letter 
        for each new word, with no underscores. Every letter in a word (including 
        abbreviations that are never spelt out) after the first should be in lower case.
        """
    
    def category(self):
        return "typedef_declaration"

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
        