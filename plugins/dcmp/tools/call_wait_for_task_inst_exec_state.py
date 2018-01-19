# encoding: utf-8

import sys
import os
import datetime,time
from dateutil.relativedelta import relativedelta
from optparse import OptionParser
from optparse import OptionGroup
reload(sys)  
sys.setdefaultencoding('utf8') 

from airflow import settings




if __name__ == "__main__":
    script_folder=settings.DAGS_FOLDER+"/plugins/dcmp/tools"
    print script_folder
    sys.path.append(script_folder)
    import wait_for_task_inst_exec_state

    parser = wait_for_task_inst_exec_state.getOptionParser()
    options, args = parser.parse_args(sys.argv[1:])
    op=wait_for_task_inst_exec_state.param_parser(options)
    wait_for_task_inst_exec_state.waiting_task_inst(op)



