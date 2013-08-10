import os
import logging
import ConfigParser

class CSCRuleFile:
    """
    The rule file is formatted as:
    
    [rule_1]
    description = "This is the description for rule_1" 
    enable =  True
    priority = 1
    """
    
    def __init__(self, filename):
        self._logger = logging.getLogger("rule")
        
        self._filename = filename
        
        if not os.path.exists(self._filename):
            raise Exception("Fail to find the rule file %s" % self._filename)        

        self._config = ConfigParser.ConfigParser()
        self._config.read(self._filename)
        
    def filename(self):
        return self._filename
            
    def check_rule(self, name, description="No description", enable=True):
        if not self._config.has_section(name):
            self._config.add_section(name)
            self._config.set(name, "description", description)
            self._config.set(name, "enable", enable)
            self._config.write(open(self._filename, "w"))
            return enable
        return self._config.getboolean(name, "enable")
    
    def get_rules(self):
        rules = self._config.sections()
        ret = []
        for name in rules:
            ret.append((name, self.check_rule(name)))
        return ret
    
