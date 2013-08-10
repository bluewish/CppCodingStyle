from rules import CSCRuleBase 
import re

#re_macro_def = re.compile(r"([^ ()]+)(\([^()]+\))?\s+(.*)?")
re_numeric = re.compile(r"-?\d+[LlSs]?")
def is_numeric(num_str):
    num_str.strip()
    match_obj = re_numeric.match(num_str)
    if None != match_obj:
        return True
    return False

def extract_macroname(macro_str):
    if None == macro_str:
        return None
    name_part = None
    param_part = None
    body_part = None
    macro_str.strip()
    first_space_pos = macro_str.find(" ")
    if first_space_pos < 0:
        name_part = macro_str
        return (name_part, param_part, body_part)
    first_left_parentheses_pos = macro_str.find("(", 0, first_space_pos)
    if first_left_parentheses_pos < 0:
        name_part = macro_str[:first_space_pos]
        body_part = macro_str[first_space_pos+1:]
        body_part.strip()
        return (name_part, param_part, body_part)
    first_right_parentheses_pos = macro_str.find(") ", first_left_parentheses_pos+1)
    if first_right_parentheses_pos < 0:
        return None
    name_part = macro_str[:first_left_parentheses_pos]
    param_part = macro_str[first_left_parentheses_pos:first_right_parentheses_pos+1]
    body_part = macro_str[first_right_parentheses_pos+1:]
    return (name_part, param_part, body_part)
    
    

class rule_macro_definition(CSCRuleBase):
    rule_re = re.compile("[A-Z0-9_]+")
    
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return " all upper-case with underscores between words "
        
    def category(self):
        return "macro_definition"

    def execute(self, item_name, line, column, source, ext_param):
        #print file, col, row, name
        #macro_name = source[column-1:].strip()
        macro_str = source[column-1:].strip()
        macro_parts = extract_macroname(macro_str)
        if None == macro_parts:
            return None
        (macro_name, param_part, body_part) = macro_parts
        issue_records = []
        # #define sprint _sprint   and so on, should NOT be consider as an error
        if None!=param_part or body_part == None or is_numeric(body_part):
            if self.rule_re.match(macro_name) == None:
                self._logger.error("Find exception: %s" % macro_name)
                #self.db().report_issue(file_name, line, column, self.name(), source)
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record)
        return issue_records        