# encoding: utf-8

import sys
import os
import datetime,time
from dateutil.relativedelta import relativedelta
reload(sys)  
sys.setdefaultencoding('utf8') 

from airflow import settings
from airflow.hooks.mysql_hook import MySqlHook
from airflow.hooks.base_hook import CONN_ENV_PREFIX


MYSQL_CONN_ID = "dag_creation_manager_plugin_wait_for_task_inst_exec_state"


def get_mysql_hook():
    os.environ[CONN_ENV_PREFIX + MYSQL_CONN_ID.upper()] = settings.SQL_ALCHEMY_CONN
    return MySqlHook(mysql_conn_id=MYSQL_CONN_ID)



def param_parser(params):
    # init param value for the blank keys
    # 频率默认为daily
    if not params.has_key('frequency'):
        params['frequency']='daily'
    if not params.has_key('state'):
        params['state']='success'
    if not params.has_key('overtime_num'):
        params['overtime_num']=1440
    if not params.has_key('overtime_duration'):
        params['overtime_duration']=60

    if isinstance(params['execution_date']  ,datetime.datetime):
        execution_date=params['execution_date']
    else:
        execution_date=datetime.datetime.strptime(params['execution_date'],'%Y-%m-%d %H:%M:%S')

    #(params.execution_date+relativedelta(days=+1)).strftime("%Y-%m-%d %H:%M:%S")      
    if params['frequency']=='daily':
         params['execution_date_begin']=execution_date.strftime("%Y-%m-%d 00:00:00")
         params['execution_date_end']=(execution_date+relativedelta(days=+1)).strftime("%Y-%m-%d 00:00:00")
    if params['frequency']=='last_daily':
         params['execution_date_begin']=(execution_date+relativedelta(days=-1)).strftime("%Y-%m-%d 00:00:00")
         params['execution_date_end']=execution_date.strftime("%Y-%m-%d 00:00:00")
    elif params['frequency']=='monthly':
         params['execution_date_begin']=execution_date.strftime("%Y-%m-01 00:00:00")
         params['execution_date_end']=(execution_date+relativedelta(months=+1)).strftime("%Y-%m-01 00:00:00")
    elif params['frequency']=='last_monthly':
         params['execution_date_begin']=(execution_date+relativedelta(months=-1)).strftime("%Y-%m-01 00:00:00")
         params['execution_date_end']=execution_date.strftime("%Y-%m-01 00:00:00")
    elif params['frequency']=='yearly':
         params['execution_date_begin']=execution_date.strftime("%Y-01-01 00:00:00")
         params['execution_date_end']=(execution_date+relativedelta(years=+1)).strftime("%Y-01-01 00:00:00")
    elif params['frequency']=='last_yearly':
         params['execution_date_begin']=(execution_date+relativedelta(years=-1)).strftime("%Y-01-01 00:00:00")
         params['execution_date_end']=execution_date.strftime("%Y-01-01 00:00:00")
    elif params['frequency']=='hourly':
         params['execution_date_begin']=execution_date.strftime("%Y-%m-%d %H:00:00")
         params['execution_date_end']=(execution_date+relativedelta(hours=+1)).strftime("%Y-%m-%d %H:00:00")
    elif params['frequency']=='custom':
        if not params.has_key('execution_date_begin'):
            raise Exception("frequency=custom时,需设置execution_date_begin值;\n格式：datetime或%Y-%m-%d %H:%M:%S格式的string;\n取值:可参考dag_id的动态execution_date值,进行运算操作；不建议使用静态值 ")
        if not params.has_key('execution_date_end'):
            raise Exception("frequency=custom时,需设置execution_date_begin值;\n格式：datetime或%Y-%m-%d %H:%M:%S格式的string;\n取值:可参考dag_id的动态execution_date值,进行运算操作；不建议使用静态值 ")

        if isinstance(params['execution_date_begin'],datetime.datetime):
            params['execution_date_begin']=params['execution_date_begin'].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(params['execution_date_end'],datetime.datetime):
            params['execution_date_end']=params['execution_date_end'].strftime("%Y-%m-%d %H:%M:%S")                 
    else:
        raise Exception("frequency取值无效[daily,last_daily,monthly,last_monthly,yearly,last_yearly,hourly,custom;缺省为daily]")

    return params

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


def task_instance_exec_state_exists(params):
    sql_exec=""" SELECT COUNT(1) AS CNT FROM (
                SELECT 1 as c FROM task_instance 
                  WHERE dag_id = '%s'
                  AND task_id = '%s'
                  AND state = '%s' 
                  AND execution_date >= '%s'
                  AND execution_date < '%s' ) QU
                """ % (params['dag_id']
                    ,params['task_id']
                    ,params['state']
                    ,params['execution_date_begin']
                    ,params['execution_date_end'])
    # 是否存在已运行状态的task_instance          
    result=run_sql(sql_exec)[0][0]
    return True if result > 0 else  False   

# params为解析好的参数对
def waiting_task_inst(params):
    re = task_instance_exec_state_exists(params)
    sum = 0
    while ( not(re) and sum < params['overtime_num'] ):
        time.sleep( params['overtime_duration'] )
        re = task_instance_exec_state_exists(params)
        sum += 1
        print "等待%s.%s,[%s]" %(params['dag_id']
                                 ,params['task_id']
                                 ,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                )
    if sum > 0 : 
        print "总共等待时间为:%s分钟" %(params['overtime_num'])
    if not(re):
        raise Exception("作业执行超时")#异常被抛出，print函数无法执行
    return True    


def main(params):

    op=param_parser(params)
    #print op
    #print '#######33333'
    waiting_task_inst(op)

if __name__ == "__main__":
    print sys.argv[1:]
    params={}
    params['frequency']='daily'
    params['dag_id']='dag002'
    params['task_id']='end'
    params['execution_date']='2018-02-23 12:13:00'
    params['state']='success'
    params['overtime_num']=5
    params['overtime_duration']=2
    params['execution_date_begin']='2018-02-23 12:13:00'
    params['execution_date_end']='2018-02-23 12:13:00'
    main(params)






