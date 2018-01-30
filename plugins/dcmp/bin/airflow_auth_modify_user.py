# encoding: utf-8

import airflow
from airflow import models, settings
from airflow.contrib.auth.backends.password_auth import PasswordUser
#修改已存在的用户信息
session = settings.Session()
u=session.query(PasswordUser).filter_by(username="admin").first()  
u.password = '123456'
u.email = 'admin@example.com'
session.commit()
session.close()




