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
from airflow.hooks.mysql_hook import MySqlHook
from airflow.hooks.base_hook import CONN_ENV_PREFIX


MYSQL_CONN_ID = "dag_creation_manager_plugin_wait_for_task_inst_exec_state"


def get_mysql_hook():
    os.environ[CONN_ENV_PREFIX + MYSQL_CONN_ID.upper()] = settings.SQL_ALCHEMY_CONN
    return MySqlHook(mysql_conn_id=MYSQL_CONN_ID)


def getOptionParser():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    prodEnvOptionGroup = OptionGroup(parser, "Product Env Options",
                                     "Normal user use these options to set jvm parameters, job runtime mode etc. "
                                     "Make sure these options can be used in Product Env.")
    prodEnvOptionGroup.add_option("--ed","--execution_date", metavar="<execution_date>",
                                  action="store", dest="execution_date",
                                  help="")
    prodEnvOptionGroup.add_option("--fr","--frequency", metavar="<frequency>",
                                  action="store", dest="frequency",
                                  help="")

    prodEnvOptionGroup.add_option("--di","--dag_id", metavar="<dag_id>",
                                  action="store", dest="dag_id",
                                  help="")
    #job参数
    prodEnvOptionGroup.add_option("--ti","--task_id", metavar="<task_id>",
                                  action="store", dest="task_id",type="string",
                                  help='') 
    prodEnvOptionGroup.add_option("--st","--state", metavar="<state>",
                                  action="store", dest="state",
                                  help="")
    prodEnvOptionGroup.add_option("--eb","--execution_date_begin", metavar="<execution_date_begin>",
                                  action="store", dest="execution_date_begin",
                                  help="")
    prodEnvOptionGroup.add_option("--ee","--execution_date_end", metavar="<execution_date_end>",
                                  action="store", dest="execution_date_end",
                                  help="")
    prodEnvOptionGroup.add_option("--ov","--overtime", metavar="<overtime(minutes)>",
                                  action="store", dest="overtime",
                                  help="")
    parser.add_option_group(prodEnvOptionGroup)
    return parser

def param_parser(options):
    # init param value for the blank keys
    # 频率默认为daily
    if (not hasattr(options, 'frequency')) or (not options.frequency):
        setattr(options, 'frequency',  'daily' )

    if (not hasattr(options, 'state')) or (not options.state):
        setattr(options, 'state', 'success' )
    # 等待task instance的总时间为1天(60s * 1440)    
    if (not hasattr(options, 'overtime')) or (not options.overtime):
        setattr(options, 'overtime', 1440) 

    if isinstance(options.execution_date,datetime.datetime):
        execution_date=options.execution_date
    else:
        execution_date=datetime.datetime.strptime(options.execution_date,'%Y-%m-%d %H:%M:%S')

    #(options.execution_date+relativedelta(days=+1)).strftime("%Y-%m-%d %H:%M:%S")      
    if options.frequency=='daily':
         options.execution_date_begin=execution_date.strftime("%Y-%m-%d 00:00:00")
         options.execution_date_end=(execution_date+relativedelta(days=+1)).strftime("%Y-%m-%d 00:00:00")
    elif options.frequency=='monthly':
         options.execution_date_begin=execution_date.strftime("%Y-%m-01 00:00:00")
         options.execution_date_end=(execution_date+relativedelta(months=+1)).strftime("%Y-%m-01 00:00:00")
    elif options.frequency=='yearly':
         options.execution_date_begin=execution_date.strftime("%Y-01-01 00:00:00")
         options.execution_date_end=(execution_date+relativedelta(years=+1)).strftime("%Y-01-01 00:00:00")
    elif options.frequency=='hourly':
         options.execution_date_begin=execution_date.strftime("%Y-%m-%d %H:00:00")
         options.execution_date_end=(execution_date+relativedelta(hours=+1)).strftime("%Y-%m-%d %H:00:00")
    elif options.frequency=='custom':
        if isinstance(options.execution_date_begin,datetime.datetime):
            options.execution_date_begin=options.execution_date_begin.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(options.execution_date_end,datetime.datetime):
            options.execution_date_end=options.execution_date_end.strftime("%Y-%m-%d %H:%M:%S")   
    else:
        raise Exception("frequency取值无效[daily,monthly,yearly,hourly,custom;缺省为daily]")

    return options

def run_sql(sql, ignore_error=False):
    hook = get_mysql_hook()
    print "sql:\n%s" % sql
    try:
        res = hook.get_records(sql)
    except Exception as e:
        if not ignore_error:
            raise e
        res = None
    print res
    return res


def task_instance_exec_state_exists(options ):
    sql_exec=""" SELECT COUNT(1) AS CNT FROM (
                SELECT 1 as c FROM task_instance 
                  WHERE dag_id = '%s'
                  AND task_id = '%s'
                  AND state = '%s' 
                  AND execution_date >= '%s'
                  AND execution_date < '%s' ) QU
                """ % (options.dag_id
                    ,options.task_id
                    ,options.state
                    ,options.execution_date_begin
                    ,options.execution_date_end)
    # 是否存在已运行状态的task_instance          
    result=run_sql(sql_exec)[0][0]
    return True if result > 0 else  False   

# options为解析好的参数对
def waiting_task_inst(options):
    re = task_instance_exec_state_exists(options)
    sum = 0
    while ( not(re) and sum < options.overtime ):
        time.sleep( 60 )
        re = task_instance_exec_state_exists(options)
        sum += 1
        print "等待%s.%s,[%s]" %(options.dag_id
                                 ,options.task_id
                                 ,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                )
    if sum > 0 : 
        print "总共等待时间为:%s分钟" %(options.overtime)
    if not(re):
        raise Exception("作业执行超时")#异常被抛出，print函数无法执行
    return True    


def main(*params):

    parser = getOptionParser()
    #sys.argv[1:]
    options, args = parser.parse_args(params)
    print '#######11111'
    print options
    print '#######22222'
    op=param_parser(options)
    print op
    print '#######33333'
    waiting_task_inst(op)

if __name__ == "__main__":
    print sys.argv[1:]
    main()








