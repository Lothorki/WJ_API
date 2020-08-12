from xlutils.copy import copy
from core.util import *
import time
from core.client import *
import json
import Config as Config
from core.reporter import *

tmp = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
reportname = '自动化测试报告'
Config.ACCOUNT = get_gloable_data('账号配置')
Config.GLOBAL_DATA = get_gloable_data('全局变量')
Config.DB_PARAMS = get_gloable_data('数据库配置')


Config.TEMPLATES = get_data_from_sheet('接口模板')
work_book = xlrd.open_workbook('./cases/接口测试用例.xls')
workbook_new = copy(work_book)
names = work_book.sheet_names()
names.remove('账号配置')
names.remove('全局变量')
names.remove('数据库配置')
names.remove('接口模板')

start_time = time.time()

case = {'case_id': 'xxx', 'method': 'get', 'body_type': 'xxx', 'params': 'xxx',
        'headers':'xxx', 'depends':'xxx', 'status': 'xxx', 'res_time': 'xxx',
        'resCode': 'xxx', 'check1':'xxx', 'zuh_charge': 'xxx', 'zdh_charges': 'xxx',
        'zdh_counts': 'xxx', 'zuh_keys':'xxx', 'zdh_keys': 'xxx', 'check_sign': 'xxx',
        'main_ds': 'xxx', 'bak_ds': 'xxx'}
def run_case(case):
	flag = True
	if isinstance(case.get('用例编号'), float):
		case_id = str(int(case.get('用例编号')))
	else:
		case_id = str(case.get('用例编号'))
