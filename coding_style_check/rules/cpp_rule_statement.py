'''
Created on 2012-1-9

@author: lwu23X
'''
from rules import CSCRuleBase 
from clang.cindex import CursorKind
import re

def is_function_def(kind):
    return CursorKind.FUNCTION_DECL == kind or CursorKind.CONSTRUCTOR == kind or \
           CursorKind.DESTRUCTOR == kind or CursorKind.CXX_METHOD == kind

def is_conditional_statement(kind):
    return kind == CursorKind.IF_STMT or \
           kind == CursorKind.SWITCH_STMT or \
           kind == CursorKind.WHILE_STMT or \
           kind == CursorKind.DO_STMT or \
           kind == CursorKind.FOR_STMT
           
def exist_any_leading_nonspace(line_str, col): # here col start from 1
    sub_str = line_str[ : col -1]
    for char in sub_str:
        if char != ' ':
            return True
    return False

def only_one_statement(compound_statement_body_str):
    compound_statement_body_str.strip()
    pos = compound_statement_body_str.find(";")
    if pos < 0:
        return True
    sec_pos = compound_statement_body_str.find(";", pos + 1)
    if sec_pos < 0:
        return True
    return False    

class rule_statement_indent(CSCRuleBase):
    '''
    classdocs
    '''


    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "each indent should contain 4 spaces, not any tab"
    
    def category(self):
        return "statement"

    def execute(self, item_name, line, column, source, ext_param):
        issue_records = []
        # all leading spaces checking
        if exist_any_leading_nonspace(source, column):
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
            issue_records.append(issue_record)
        (gfather_info, father_info, node_ext_info) = ext_param
        if None == father_info:
            return issue_records     
        (nth_child, p_kind, p_start_ln, p_start_col, p_end_ln, p_end_col) = father_info
        (this_kind, this_end_ln, this_end_col) = node_ext_info
        
        if CursorKind.NULL_STMT == this_kind:
            return [] # [TEMP]
        if CursorKind.COMPOUND_STMT == p_kind:
            (g_kind, g_start_ln, g_start_col) = gfather_info
            #if is_conditional_statement(g_kind) or CursorKind.CXX_TRY_STMT == g_kind:
            #    col = g_start_col
            #elif CursorKind.CXX_CATCH_STMT == g_kind:
            #    #[TODO]
            #    pass
            #elif g_start_ln == p_start_ln:
            #    col = g_start_col
            #else:
            #   col = p_start_col
            col = (p_end_col - 1)
            if (p_start_ln==p_end_ln and p_end_ln==line and line==this_end_ln) and \
                only_one_statement(source[p_start_col+1:p_end_col]):
                return []
            if column != (col + 4):
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                issue_records.append(issue_record)
        elif CursorKind.COMPOUND_STMT == this_kind:
            ###CursorKind.COMPOUND_STMT == p_kind impossible in fact, it has been processed by if CursorKind.COMPOUND_STMT == p_kind
            if CursorKind.IF_STMT == p_kind and nth_child > 1: ###  else{} belong to this case
                #[TODO] it has to be known its last sibling's line
                pass 
            elif is_function_def(p_kind):
                if this_end_col != p_end_col:
                    issue_record = (this_end_ln, this_end_col, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
                if column != p_start_col:
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "curly braces should be put on separate lines for function defination body")
                    issue_records.append(issue_record)
            elif is_conditional_statement(p_kind) or CursorKind.CXX_TRY_STMT == p_kind:
                if this_end_col != p_end_col:
                    issue_record = (this_end_ln, this_end_col, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
                if line != p_start_ln:
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
            elif CursorKind.CXX_CATCH_STMT == p_kind:
                #[TODO] col check
                if line != p_start_ln:
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
            else:
                if column != (p_start_col + 4):
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
                if this_end_col != (p_start_col + 4):
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
        elif CursorKind.CXX_CATCH_STMT == this_kind: # its parent will be CursorKind.CXX_TRY_STMT
            #[TODO]
            if CursorKind.CXX_TRY_STMT == p_kind:
                if this_end_col != p_end_col:
                    issue_record = (this_end_ln, this_end_col, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
                #if line != p_end_ln:
                #    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                #    issue_records.append(issue_record)
                #[TODO] get its last sibling (COMPOUND_STMT: try body) and then do check
        elif CursorKind.IF_STMT == p_kind:  
            if CursorKind.IF_STMT == this_kind:# else if(){ will belong to this case
                if nth_child==1:
                    if p_end_ln != line:
                        issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                        issue_records.append(issue_record)
                else:
                    #[TODO] its' sibling's position info should be known
                    pass
            
            elif CursorKind.BREAK_STMT == this_kind or CursorKind.CONTINUE_STMT == this_kind or CursorKind.RETURN_STMT == this_kind:
                if line == p_start_ln and line != p_end_ln:
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "")
                    issue_records.append(issue_record)
        return issue_records
    
class rule_1_space_between_conditional_keyword_and_parentheses:
    '''
    classdocs
    '''
    
    rule_if_re = re.compile("if \(")
    rule_while_re = re.compile("while \(")
    rule_switch_re = re.compile("switch \(")
    rule_for_re = re.compile("for \(")
    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "there should be only one space between if/while/for/switch and parentheses"
    
    def category(self):
        return "statement"

    def execute(self, item_name, line, column, source, ext_param):
        (gfather_info, father_info, node_ext_info) = ext_param
        (nth_child, p_kind, p_start_ln, p_start_col, p_end_ln, p_end_col) = father_info
        (this_kind, this_end_ln, this_end_col) = node_ext_info
        issue_records = []
        condition_str = source[column - 1 :]
        if this_kind == CursorKind.IF_STMT:
            m = self.rule_if_re.search(condition_str)
            if m == None or len(m.groups()[0]) != 1:
                self._logger.error("Find exception: (%d:%d) " % (line, column))
                #self.db().report_issue(file_name, line, column, self.name(), source) 
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record)   
        elif this_kind == CursorKind.FOR_STMT:
            m = self.rule_for_re.search(condition_str)
            if m == None or len(m.groups()[0]) != 1:
                self._logger.error("Find exception: (%d:%d) " % (line, column))
                #self.db().report_issue(file_name, line, column, self.name(), source) 
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record)   
        elif this_kind == CursorKind.WHILE_STMT:
            m = self.rule_while_re.search(condition_str)
            if m == None or len(m.groups()[0]) != 1:
                self._logger.error("Find exception: (%d:%d) " % (line, column))
                #self.db().report_issue(file_name, line, column, self.name(), source) 
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record)   
        elif this_kind == CursorKind.SWITCH_STMT:
            m = self.rule_switch_re.search(condition_str)
            if m == None or len(m.groups()[0]) != 1:
                self._logger.error("Find exception: (%d:%d) " % (line, column))
                #self.db().report_issue(file_name, line, column, self.name(), source) 
                issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                issue_records.append(issue_record) 
        elif this_kind == CursorKind.DO_STMT:
            #[TODO]
            pass  
            
        return issue_records
    
def pos_pair_of_parentheses_and_brace(line_str):
    pos1 = line_str.rfind('{')
    if pos1 > 0:
        pos2 = line_str.rfind('(')
        return (pos2, pos1)
    else:
        pos1 = line_str.rfind('}')
        if pos1 > 0:
            pos2 = line_str.rfind(')')
            return (pos1, pos2)
    return None
    
class rule_1_space_between_parentheses_and_brace:
    '''
    classdocs
    '''

    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "there should be only one space between parentheses and brace"
    
    def category(self):
        return "statement"

    def execute(self, item_name, line, column, source, ext_param):
        pos_pair = pos_pair_of_parentheses_and_brace(source)
        if None == pos_pair:
            return []
        issue_records = []
        (beg_pos, end_pos) = pos_pair
        if end_pos != (beg_pos + 1) or source[beg_pos + 1] != ' ':
            issue_record = (line, beg_pos + 1, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record) 
        return issue_records
    
def last_pos_of_statement_line(line_str):
    pos = line_str.rfind(';')
    if pos >= 0:
        return pos
    pos = line_str.rfind('{')
    if pos >= 0:
        return pos
    pos = line_str.rfind('}')
    if pos >= 0:
        return pos
    #pos = line_str.rfind(')') # remove temp, there may be function called directly in conditional parameter list
    #if pos >= 0:
    #    return pos
    return -1


class rule_no_pure_white_blank_at_rear_of_statement_line(CSCRuleBase):
    '''
    classdocs
    '''


    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "there should be no pure white blank at the rear of a statement line"
    
    def category(self):
        return "statement"

    def execute(self, item_name, line, column, source, ext_param):
        source = source.strip("\n")
        (gfather_info, father_info, node_ext_info) = ext_param
        (nth_child, p_kind, p_start_ln, p_start_col, p_end_ln, p_end_col) = father_info
        (this_kind, this_end_ln, this_end_col) = node_ext_info
        if this_kind == CursorKind.NULL_STMT:
            return []
        if this_kind != CursorKind.COMPOUND_STMT and p_kind != CursorKind.COMPOUND_STMT:
            return []
        pos = last_pos_of_statement_line(source) 
        if pos < 0:
            return []
        issue_records = []
        sub_str = source[pos + 1:]
        if len(sub_str) > 0 and sub_str.isspace():
            issue_record = (line, pos + 1, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record) 
        return issue_records
        