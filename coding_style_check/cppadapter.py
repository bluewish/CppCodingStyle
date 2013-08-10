import logging
import sys
import os
import traceback

import csc
import clang.cindex
import rules
from collections import deque
            
if hasattr(sys, "frozen"):
    app_path = os.path.abspath(os.path.dirname(sys.executable))
else:
    app_path = os.path.abspath(os.path.dirname(__file__))
    
def is_identical_node(node1, node2):
    if node1.extent != None and node2.extent != None:
        return node1.extent.start.line == node2.extent.start.line and \
               node1.extent.start.column == node2.extent.start.column and \
               node1.extent.end.line == node2.extent.end.line and \
               node1.extent.end.column == node2.extent.end.column and\
               node1.kind == node2.kind
    else:
        return False
    
def is_statement(kind):
    return kind == clang.cindex.CursorKind.IF_STMT or \
           kind == clang.cindex.CursorKind.SWITCH_STMT or \
           kind == clang.cindex.CursorKind.CASE_STMT or \
           kind == clang.cindex.CursorKind.DEFAULT_STMT or \
           kind == clang.cindex.CursorKind.WHILE_STMT or \
           kind == clang.cindex.CursorKind.DO_STMT or \
           kind == clang.cindex.CursorKind.FOR_STMT or \
           kind == clang.cindex.CursorKind.BREAK_STMT or \
           kind == clang.cindex.CursorKind.CONTINUE_STMT or \
           kind == clang.cindex.CursorKind.RETURN_STMT or \
           kind == clang.cindex.CursorKind.CXX_TRY_STMT or \
           kind == clang.cindex.CursorKind.CXX_CATCH_STMT or \
           kind == clang.cindex.CursorKind.CXX_FOR_RANGE_STMT or \
           kind == clang.cindex.CursorKind.DECL_STMT or \
           kind == clang.cindex.CursorKind.COMPOUND_STMT
        
class CodingStyleCheckerAdapterCpp(csc.CodingStyleCheckerAdapter):
    _rules = {}
    max_record_num_in_memory = 512
    
    def __init__(self, file_name, db, args=None):
        super(CodingStyleCheckerAdapterCpp, self).__init__(file_name, db, args)
        fd = open(file_name, "r")
        self._lines = fd.readlines()
        fd.close()
        self._issue_records = [] 
        self._macro_records = []  #(start_line_no, start_col_no, end_line_no, end_col_no)
        self._node_relations = deque() #(node_kind, start_line_no, start_col_no, end_line_no, end_col_no, processing_child_nth)
        self._tmp_log_filename = file_name + ".log" # temp
        if os.path.isfile(self._tmp_log_filename):
            os.remove(self._tmp_log_filename)
    
    def __del__(self):
        self.dump_to_db()
    
    def process_node_relation(self, parent_node, this_node):
        if clang.cindex.CursorKind.TRANSLATION_UNIT == parent_node.kind:
            self._node_relations = []
        nth = 0
        left_sibling_node = None
        fd = open(self._tmp_log_filename, "a")
        if this_node.extent != None:
            this_node_record = (this_node, 0)
            if parent_node.extent != None and parent_node.extent.start != None and parent_node.extent.start.file != None:
                while len(self._node_relations) > 0:
                    node_record = self._node_relations.pop()
                    (node, num) = node_record
                    left_sibling_node = node
                    if is_identical_node(node, parent_node):         
                        nth = num + 1
                        node_record = (node, nth)
                        self._node_relations.append(node_record)
                        break
            self._node_relations.append(this_node_record)
            ##[TEMP] print node stack
            fd.write( "\ncurrent stack:\n")
            for node_record in self._node_relations:
                (node, num) = node_record
                fd.write( "%s[(%d,%d)~(%d,%d)]:%d \n" %(node.kind, \
                                                  node.extent.start.line,node.extent.start.column,\
                                                  node.extent.end.line,node.extent.end.column, \
                                                  num) )
            fd.close()
            return nth
        fd.close()
        return -1
    
    def add_issue_record(self, issue_record): 
        self._issue_records.append(issue_record)
        if len(self._issue_records) >= CodingStyleCheckerAdapterCpp.max_record_num_in_memory:
            self.dump_to_db()
            
    def add_issue_records(self, issue_records): 
        self._issue_records.extend(issue_records)
        if len(self._issue_records) >= CodingStyleCheckerAdapterCpp.max_record_num_in_memory:
            self.dump_to_db()
            
    def dump_to_db(self):
        if len(self._issue_records) > 0:
            #(line, column, rule, source, errorlevel, description)
            self.db().report_issues(self.filename(), self._issue_records)
            self._issue_records = []
            
    def add_macro_instantiation_record(self, start_line_no, start_col_no, end_line_no, end_col_no):
        macro_record = (start_line_no, start_col_no, end_line_no, end_col_no)
        self._macro_records.append(macro_record)
        
    def is_macro_extension(self, start_line_no, start_col_no, end_line_no, end_col_no):
        for (sln_no, scol_no, eln_no, ecol_no) in self._macro_records:
            if sln_no == start_line_no and scol_no == start_col_no and \
               eln_no == end_line_no and ecol_no == end_col_no:
                return True
        return False
       
    @staticmethod 
    def get_filter():
        """ overwrite parent's method. """
        return ".hpp;.cpp"
    
    def analysis(self):
        if not super(CodingStyleCheckerAdapterCpp, self).analysis():
            return False
         
        logger = logging.getLogger("AdapterCpp")
        
        self._run_rule("file", 0, 0, self._filename, self._filename)
        index_obj = clang.cindex.Index.create()
        
        clang_args = []
        if self.args() != None:
            if self.args().has_key("includes"):
                for item in self.args()["includes"]:
                    clang_args.append("-I%s" % item)
            if self.args().has_key("macros"):
                for key in self.args()["macros"]:
                    if self.args()["macros"][key] == None:
                        clang_args.append("-D%s" % key)
                    else:
                        clang_args.append("-D%s=%s" % (key, self.args()["macros"][key]))
        
        logger.debug("Analysis file %s with args %s" % (self.filename(), clang_args))
        tu = index_obj.parse(self.filename(), clang_args, options=1)
        if tu == None:
            return
        
        clang.cindex.Cursor_visit(
                tu.cursor,
                clang.cindex.Cursor_visit_callback(self.callexpr_visitor),
                None)           
 
#enum CXChildVisitResult {
#   /**
#    * \brief Terminates the cursor traversal.
#    */
#   CXChildVisit_Break,
#   /**
#    * \brief Continues the cursor traversal with the next sibling of
#    * the cursor just visited, without visiting its children.
#    */
#   CXChildVisit_Continue,
#   /**
#    * \brief Recursively traverse the children of this cursor, using
#    * the same visitor and client data.
#    */
#   CXChildVisit_Recurse
# };       
        
    def callexpr_visitor(self, node, parent, userdata):

        if node.location.file == None: 
            return 2
        
        if node.location.file.name.lower() != self.filename().lower():
            return 2
        
        #[TEMP] log
        fd = open(self._tmp_log_filename, "a")
        fd.write("\n\n")
        if parent.kind != None:
            fd.write("parent node kind:%s\n" %(parent.kind))
        if parent.location.file != None:
            fd.write("parent node file:%s(%d,%d)\n" %(parent.location.file.name, parent.location.line, parent.location.column) )
            fd.write( "parent node context: start(%d,%d) ~ end(%d,%d)\n" %(parent.extent.start.line,parent.extent.start.column,\
                                                                      parent.extent.end.line,parent.extent.end.column)  )           
        if parent.spelling != None:         
            fd.write( "parent node spelling:%s\n" %(parent.spelling) )
         
        if node.kind != None:
            fd.write( "this node kind:%s\n" %(node.kind)   )
        if node.location.file != None:
            fd.write( "this node file:%s(%d,%d)\n" %(node.location.file.name, node.location.line, node.location.column) )
            fd.write( "this node context: start(%d,%d) ~ end(%d,%d)\n" %(node.extent.start.line,node.extent.start.column,\
                                                                   node.extent.end.line,node.extent.end.column)   )                
        if node.spelling != None:
            fd.write( "this node spelling:%s\n" %(node.spelling))
        
        if node.kind == clang.cindex.CursorKind.MACRO_INSTANTIATION:
            fd.write( "this node MACRO_INSTANTIATION, so record its position.\n" )
            self.add_macro_instantiation_record(node.extent.start.line,node.extent.start.column,\
                                                node.extent.end.line,node.extent.end.column) 
            fd.close()
            return 2
        
        if self.is_macro_extension(node.extent.start.line,node.extent.start.column,\
                                   node.extent.end.line,node.extent.end.column):
            fd.write( "this node is macro extension.\n" )
            fd.close()
            return 1
        
        fd.close()
        
        self.process_node_relation(parent, node) # node stack, because visit order is pre-order, so stack can be traced
            
        if node.kind == clang.cindex.CursorKind.NAMESPACE:
            self._run_rule("namespace", node.location.line,
                           node.location.column, node.spelling, parent.spelling)
        elif node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            self._run_rule("function_declaration", node.location.line,
                           node.location.column, node.spelling, parent.spelling)
        elif node.kind == clang.cindex.CursorKind.CLASS_DECL:
            self._run_rule("class_declaration", node.location.line,
                           node.location.column, node.spelling, parent.spelling)    
        elif node.kind == clang.cindex.CursorKind.VAR_DECL:
            pre_sub_str = self._get_line(node.location.line)[0:node.location.column]
            if pre_sub_str.lower().find("const") != -1:
                self._run_rule("const_variable_declaration",  
                               node.location.line, node.location.column, node.spelling, 
                               parent.spelling)
            else:
                self._run_rule("variable_declaration", node.location.line,
                               node.location.column, node.spelling, parent.spelling)   
        elif node.kind == clang.cindex.CursorKind.ENUM_DECL:
            self._run_rule("enum_declaration", node.location.line,
                           node.location.column, node.spelling, parent.spelling)    
        elif node.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
            self._run_rule("enum_constant", node.location.line,
                           node.location.column, node.spelling, parent.spelling)                         
        elif node.kind == clang.cindex.CursorKind.STRUCT_DECL:
            self._run_rule("struct_declaration", node.location.line,
                           node.location.column, node.spelling, parent.spelling)     
        elif node.kind == clang.cindex.CursorKind.TYPEDEF_DECL:
            self._run_rule("typedef_declaration", node.location.line,
                           node.location.column, node.spelling, parent.spelling)   
        elif node.kind == clang.cindex.CursorKind.MACRO_DEFINITION:
            self._run_rule("macro_definition", node.location.line,
                           node.location.column, node.spelling, parent.spelling)  
        elif node.kind == clang.cindex.CursorKind.PARM_DECL:
            parent_location = (parent.location.line, parent.location.column)
            self._run_rule("param_declaration", node.location.line,
                           node.location.column, node.spelling, parent_location)
        elif node.kind == clang.cindex.CursorKind.CONSTRUCTOR:
            pass  #to check whether single-param constructor has been declared with explict    
        elif node.kind == clang.cindex.CursorKind.CALL_EXPR:
            self._run_rule("call_function", node.location.line,
                           node.location.column, node.spelling, parent.spelling)   
        elif node.kind == clang.cindex.CursorKind.IF_STMT:
            self._run_rule("if_statement", node.location.line,
                           node.location.column, node.spelling, parent.spelling)
        
        elif node.kind == clang.cindex.CursorKind.BINARY_OPERATOR: # a + b     a >= b
            self._run_rule("binary_operator", node.location.line,
                           node.location.column, node.spelling, parent.spelling)  
        elif node.kind == clang.cindex.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR: # +=
            pass
        elif node.kind == clang.cindex.CursorKind.CONDITONAL_OPERATOR:  # ?:
            pass
        elif node.kind == clang.cindex.CursorKind.COMPOUND_ASSIGNMENT_OPERATOR:
            pass                                                                           
        elif node.kind == clang.cindex.CursorKind.FIELD_DECL:
            if parent.kind == clang.cindex.CursorKind.CLASS_DECL:
                self._run_rule("class_memeber_variable_declaration", node.location.line,
                               node.location.column, node.spelling, parent.spelling)
            elif parent.kind == clang.cindex.CursorKind.STRUCT_DECL:
                self._run_rule("struct_field_declaration", node.location.line,
                               node.location.column, node.spelling, parent.spelling)  
            elif parent.kind == clang.cindex.CursorKind.UNION_DECL:
                self._run_rule("union_field_declaration", node.location.line,
                               node.location.column, node.spelling, parent.spelling)
        elif node.kind == clang.cindex.CursorKind.CSTYLE_CAST_EXPR: 
            pass 
        elif node.kind == clang.cindex.CursorKind.CXX_FUNCTIONAL_CAST_EXPR: 
            pass 
        elif node.kind == clang.cindex.CursorKind.CONVERSION_FUNCTION:
            pass
        elif node.kind == clang.cindex.CursorKind.TEMPLATE_TYPE_PARAMETER:
            pass 
        elif node.kind == clang.cindex.CursorKind.TEMPLATE_NON_TYPE_PARAMETER:
            pass 
        elif node.kind == clang.cindex.CursorKind.TEMPLATE_TEMPLATE_PARAMTER:
            pass
        elif node.kind == clang.cindex.CursorKind.FUNCTION_TEMPLATE:
            pass 
        elif node.kind == clang.cindex.CursorKind.CLASS_TEMPLATE:
            pass 
        elif node.kind == clang.cindex.CursorKind.CLASS_TEMPLATE_PARTIAL_SPECIALIZATION:
            pass 
        elif node.kind == clang.cindex.CursorKind.CXX_ACCESS_SPEC_DECL:
            pass   
        elif node.kind == clang.cindex.CursorKind.INCLUSION_DIRECTIVE: 
            pass  ####not further recursively analyze                
        else:
            print node.kind, node.spelling, node.location.line, node.location.file
        # indent checking and so on    
        if is_statement(node.kind) or parent.kind == clang.cindex.CursorKind.COMPOUND_STMT:
            gfather_info = None
            lenth = len(self._node_relations)
            nth_child = 0
            if lenth >= 3:
                (gnode, nth_child) = self._node_relations[lenth - 3]
                gfather_info = (gnode.kind, gnode.extent.start.line, gnode.extent.start.column)
            father_info  = None   
            if lenth >= 2:
                (fnode, nth_child) = self._node_relations[lenth - 2]
                father_info = (nth_child, parent.kind, parent.extent.start.line, \
                               parent.extent.start.column, parent.extent.end.line, parent.extent.end.column)
            
            node_ext_info = (node.kind, node.extent.end.line, node.extent.end.column)
            ext_param = (gfather_info, father_info, node_ext_info)
            self._run_rule("statement", node.location.line,
                           node.location.column, node.spelling, ext_param)
            
        return 2
    
    # line passed-in is from 1,
    def _get_extent_lines(self, start_line, end_line):
        if start_line < 0 or end_line < 0 or end_line < start_line:
            return None
        if end_line > len(self._lines):
            return None   
        total_line = self._lines[start_line - 1]
        line_no = start_line + 1
        while(line_no <= end_line):  
            total_line = total_line + "\n" +  self._lines[line_no - 1] 
            line_no = line_no + 1  
        return total_line
    
    def _get_line(self, line): ### line passed-in start from 1 not 0
        if line <= 0:
            return None       
        return self._lines[line -1]
    
    #[TODO] this function should be changed some time later
    def _run_rule(self, category_name, line, column, name, ext_param=None):
        if not self._rules.has_key(category_name):
            return
            
        category_dict = self._rules[category_name]
        for rule_item in category_dict.values():
            try:
                #[TEMP] later execute parameter list will change a little
                issue_records = rule_item.execute(name,
                                                  line,
                                                  column,
                                                  self._get_line(line),
                                                  ext_param)
                self.add_issue_records(issue_records)
            except Exception as ex:
                logging.getLogger().error("".join(traceback.format_exception(*sys.exc_info())))
                print ex
        return 2  # means continue visiting recursively
    
    @staticmethod
    def init_rules(rule_file, db):
        rule_files = []
        for root, dirs, files in os.walk(os.path.join(app_path, "rules")):
            for dir_name in dirs:
                if dir_name.lower() in [".svn", ".git", "_svn"]:
                    dirs.remove(dir_name)
            for file in files:
                base_name, ext_name = os.path.splitext(file)
                if base_name == "__init__":
                    continue
                if ext_name.lower() == ".py":
                    rule_files.append(base_name)
        rule_classes = []
        mod = __import__("rules")
        for file_name in rule_files:
            mod = __import__(".".join(("rules", file_name)))
            keys = mod.__dict__.keys()
            items = mod.__dict__.items()
            print items
            if mod.__dict__.has_key(file_name):
                rule_sub_mod =  getattr(mod, file_name)
                for key in rule_sub_mod.__dict__.keys():
                    cls = getattr(rule_sub_mod, key)
                    if cls == rules.CSCRuleBase:
                        continue
                    try:
                        if issubclass(cls, rules.CSCRuleBase):
                            rule_classes.append(cls)
                    except TypeError:
                        pass
        for cls in  rule_classes:
            rule_obj = cls(db)
            
            # check if rule enabled in rule files
            if not rule_file.check_rule(rule_obj.name(), 
                                        rule_obj.description()):
                continue
            
            rule_dict = CodingStyleCheckerAdapterCpp._rules
            if not rule_dict.has_key(rule_obj.category()):
                rule_dict[rule_obj.category()] = {}
            if rule_dict[rule_obj.category()].has_key(rule_obj.name()):
                raise Exception("duplicate rule name %s is found" % rule_obj.name())
            rule_dict[rule_obj.category()][rule_obj.name()] = rule_obj
            