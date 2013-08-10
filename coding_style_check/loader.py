## @file
#  The loader for coding style checker command line tool.

import os
import sys
import logging
import traceback
from optparse import OptionParser

def get_app_path():
    """ Get dir path of this file. """
    if hasattr(sys, "frozen"):
        app_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        app_path = os.path.abspath(os.path.dirname(__file__))
    return app_path

def setup():
    """ Setup the running environment. """
    # search the clang.dll
    app_root_path = get_app_path()
    if not os.path.exists(os.path.join(app_root_path, "libs", "libclang.dll")):
        print "fail to find libclang.dll in %s" % os.path.join(app_root_path, "libs")
        return False
    
    # add clang.dll into system path
    os.environ['path'] = os.environ['path'] + ";" + os.path.join(app_root_path, "libs")
    logging.basicConfig(level=logging.NOTSET, format='%(asctime)-20s %(name)-10s %(levelname)-8s%(message)s')
    return True
    
if __name__ == "__main__":
    if not setup():
        sys.exit(-1)

    parser = OptionParser("usage: %prog [options] {configure filename}")
    parser.add_option("-r", "--rule-file", dest="rule_file", 
                        help="Specify the rule file", default=None)
    parser.disable_interspersed_args()
      
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Please specify the configure file.")
    
    conf_file = args[0]
    if not os.path.exists(conf_file):
        parser.error("fail to find the configure file %s" % conf_file)
            
    rule_file = None
    if opts.rule_file != None and not os.path.exists(opts.rule_file):
        parser.error("fail to find given rule file %s" % opts.rule_file)
    else:
        rule_file = opts.rule_file    
            
    # if did not specify the rule file use internal default rule file          
    if rule_file == None:
        rule_file = os.path.join(get_app_path(), "rule_default.txt")
        if not os.path.exists(rule_file):
            parser.error("fail to find default rule file, please specify rule file via --rule-file")
        logging.getLogger().warning("Use default rule file %s since no specify the rule file via --rule-file" % rule_file)
    
    # the dll path has been added into system path, 
    # we can import csc and cppadapter now
    import csc
    import cppadapter

    try:
        csc_obj = csc.CodingStyleChecker(rule_file, conf_file, cppadapter.CodingStyleCheckerAdapterCpp)
        csc_obj.execute()
    except Exception as ex:
        logging.getLogger().error("".join(traceback.format_exception(*sys.exc_info())))
        print ex
    
