'''
Created on 2012-1-9

@author: lwu23X
'''
from rules import CSCRuleBase 

class rule_unix_style_for_inclusion_path(CSCRuleBase):
    '''
    classdocs
    '''


    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "unix-style path seperator should be used"
    
    def category(self):
        return "inclusion_directive"

    def execute(self, item_name, line, column, source, ext_param):
        pos = item_name.find('\\')
        if pos < 0:
            return []
        issue_records = []
        issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
        issue_records.append(issue_record)
        return issue_records
    
def extract_path(include_item_str):
    beg_pos = include_item_str.find('<')
    try:
        if beg_pos >= 0:
            end_pos = include_item_str.rfind('>')
            return include_item_str[beg_pos+1, end_pos]
        else:
            beg_pos = include_item_str.find('"')
            end_pos = include_item_str.rfind('"')
            return include_item_str[beg_pos+1, end_pos]
    except:
        return None
        
    
class rule_inclusion_path_no_shortcut_dir(CSCRuleBase):
    '''
    classdocs
    '''


    def name(self):
        return self.__class__.__name__
    
    def description(self):
        return "include-directories should NOT use directory shortcuts . (the current directory) or .. (the parent directory)"
    
    def category(self):
        return "inclusion_directive"

    def execute(self, item_name, line, column, source, ext_param):
        pos = item_name.find('\\')
        if pos < 0:
            return []
        issue_records = []
        path = extract_path(item_name)
        if None == path:  
            issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
            issue_records.append(issue_record)
        else:
            path = path.replace('\\', '/')
            dir_names = path.split('/')
            for name in dir_names:
                if name == "." or name == "..":
                    issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
                    issue_records.append(issue_record)
                    break
            
        return issue_records