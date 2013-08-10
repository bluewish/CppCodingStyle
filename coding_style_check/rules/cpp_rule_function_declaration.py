from rules import CSCRuleBase 
import re

class rule_function_declaration_first_capital(CSCRuleBase):
    rule_re = re.compile("[[A-Z]+_]?[a-zA-Z]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return """
        Function names should normally be in PascalCase too, like type 
        names. This makes our functions different from system functions, which normally are all lower-case.
                Like C type names, non-static C functions may be prefixed with a name and an underscore, as in 'DCS_Initialize'"
        """
        
    def category(self):
        return "function_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        #print file, col, row, name
        issue_records = []
        if self.rule_re.match(item_name) == None:
            self._logger.error("Find exception: %s" % item_name)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records
        
class rule_function_brace_put_on_seperate_line(CSCRuleBase):
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return """ The curly braces are put on separate lines. """
        
    def category(self):
        return "function_declaration"

    def execute(self, item_name, line, column, source, ext_param):
        #print file, col, row, name
        issue_records = []
        if source.strip().endswith("{"):
            self._logger.error("Find exception: %s" % source)
            #self.db().report_issue(file_name, line, column, self.name(), source)
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        return issue_records               