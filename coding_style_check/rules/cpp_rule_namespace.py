from rules import CSCRuleBase 
import re
import os

class rule_namespace_should_in_low_case(CSCRuleBase):
	rule_re = re.compile("[a-z][a-z_]+")
	
	def name(self):
		return self.__class__.__name__
	
	def description(self):
		return "The namespace should be in low case"
	
	def category(self):
		return "namespace"
	
	def execute(self, item_name, line, column, source, ext_param):
		issue_records = []
		if self.rule_re.match(item_name) == None:
			self._logger.error("Find exception: %s" % item_name)
			#self.db().report_issue(file_name, line, column, self.name(), source)
			issue_record = (line, column, self.name(), source, CSCRuleBase.rule_errorlevel_low, "") 
			issue_records.append(issue_record)
		return issue_records