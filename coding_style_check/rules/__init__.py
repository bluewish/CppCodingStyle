
import logging

class CSCRuleBase(object):
    rule_errorlevel_high = 0
    rule_errorlevel_middle = 1 
    rule_errorlevel_low = 2 
    rule_errorlevel_warning = 3  
    def __init__(self, db):
        self._logger = logging.getLogger(self.name())
        self._db = db
        
    def db(self):
        return self._db
    
    def name(self):
        raise CSCRuleBaseException()
    
    def description(self):
        raise CSCRuleBaseException()
    
    def category(self):
        raise CSCRuleBaseException()
    
    #single item_name make no sense, so remove it, the last param will be different type in different rule.
    def execute(self, item_name, line, column, source, ext_param=None):
        raise CSCRuleBaseException()
        
   
CPP_RULE_CATEGORY = ["namespace", 
                     "function_declaration",
                     "file", 
                     "class_declaration", 
                     "variable_declaration",
                     "const_variable_declaration"
                     "class_memeber_variable_declaration",
                     "struct_field_declaration",
                     "enum_declaration",
                     "enum_constant",
                     "struct_declaration",
                     "typedef_declaration",
                     "macro_definition",
                     "param_declaration",
                     "if_statement",
                     "binary_operator"
                     ]

class CSCRuleBaseException(Exception):
    """
    This exception is used to identify the rule abstract classes
    """
    def __init__(self, message=""):
        Exception.__init__(self, message)
        
        
