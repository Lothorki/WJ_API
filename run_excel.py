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
work_book = xlrd.open_workbook('./cases/testcase.xls')
workbook_new = copy(work_book)
names = work_book.sheet_names()
names.remove('账号配置')
names.remove('全局变量')
names.remove('数据库配置')
names.remove('接口模板')

start_time = time.time()

if Config.GLOBAL_DATA.get('待运行sheet'):
	names = Config.GLOBAL_DATA.get('待运行sheet').split(',')

for n in names:
	cases = get_data_from_sheet(n)
	for index, case in enumerate(cases):
		flag = True

		if isinstance(case.get('用例编号'), float):
			case_id = n + '-' + str(int(case.get('用例编号')))
		else:
			case_id = n + '-' + str(case.get('用例编号'))
		print('--------------')
		print(case_id)
		template_name = case.get('用例模板')
		desc = case.get('用例描述')
		url = case.get('URL')
		depends = case.get('关联表达式(参数路径=临时变量名)')
		params = case.get('正文参数')
		method = case.get('请求方法')
		headers = case.get('头信息')
		body_type = case.get('参数类型')
		use_data = case.get('数据引用')
		in_signs = case.get('入参验签字段')
		out_signs = case.get('响应验签字段')
		status = case.get('响应状态码')
		res_time = case.get('响应时间')
		resCode = case.get('resCode')
		check1 = case.get('节点')
		zuh_charge = case.get('zuh计费')
		zdh_charges = case.get('zdh计费（ds_name/ds_type/charge）')
		zdh_counts = case.get('zdh记录条数')
		zuh_keys = case.get('zuh字段非空')
		zdh_keys = case.get('zdh字段非空（ds_name/ds_type/待验证字段）')
		check_sign = case.get('响应签名')
		main_ds_url = case.get('主数据源地址')
		main_ds_res = case.get('主数据源响应')
		bak_ds_url = case.get('备数据源地址')
		bak_ds_res = case.get('备数据源响应')
		log(cid=case_id, desc=desc)
		# 是否运行标志位不是  n
		if case.get('是否运行') != 'n':
			if Config.GLOBAL_DATA.get('能否直连数据库') is not None and Config.GLOBAL_DATA.get('能否直连数据库') == 'y':
				if main_ds_url and main_ds_res:
					try:
						update_mock_respond(main_ds_url, main_ds_res)
						# update_mock(main_ds)
					except:
						log(cid=case_id, result='skip', info=traceback.format_exc())
						continue

				if bak_ds_url and bak_ds_res:
					try:
						update_mock_respond(bak_ds_url, bak_ds_res)
						update_mock(main_ds)
					except:
						log(cid=case_id, result='skip', info=traceback.format_exc())
						continue

			# 模板
			if case.get('用例模板'):
				# 使用模板
				for T in Config.TEMPLATES:
					if T.get('URL') == template_name:
						url = T.get('URL')
						method = T.get('请求方法')
						body_type = T.get('参数类型')
						headers = T.get('头信息')
						in_signs = T.get('入参验签字段')

			#拼 client
			if headers:
				try:
					headers = replace_var(headers)
					headers = json.loads(headers)
				except:
					log(cid=case_id, desc=desc,  result='skip', info='接口模板头信息格式错误')
					continue
			else:
				headers = {}

			# 标准表单, JSON, xml, 复合表单, url参数
			if body_type == '标准表单':
				body_type = 'url_encoded'
			elif body_type == 'JSON':
				body_type = 'json'
			elif body_type == '复合表单':
				body_type = 'form_data'
			elif body_type == 'xml':
				body_type = 'xml'
			elif body_type == 'url参数':
				body_type = 'url参数'

			client = Http(url=url, case_id=case_id, method=method, body_type=body_type, timeout=180)
			client.set_headers(headers)
			if params:
				params = replace_var(params)
				if in_signs:
					signs = {}
					if body_type == 'url参数':
						kvs = params.split('&')
						for l in kvs:
							signs[l.split('=')[0]] = l.split('=')[1]
						sign = get_sign(signs, in_signs.split(','))
						params = params + '&sign=' + sign
					else:
						params['sign'] = get_sign(params, in_signs)
				try:
					params = json.loads(params)
					if method == 'post':
						client.set_body(params)
					elif method == 'get':
						client.params = params
				except:
					client.set_url_data(params)

			client.send()
			if depends:
				depends_list = depends.split('\n')
				for d in depends_list:
					path = d.split('=')[0]
					var_name = d.split('=')[1]
					value = client.get_response_json_value(path)
					if value is not None:
						Config.GLOBAL_DATA[var_name] = str(value)
			res_dict = client.response_jsonObj
			res_exp_sign = ''
			if out_signs:
				res_exp_sign = get_sign(res_dict, out_signs.split(',')[1:], out_signs.split(',')[0])

			# 添加检查点
			if status:
				client.check_status_code(int(status))
			else:
				client.check_status_code(200)
			if resCode:
				client.check_response_json_value('resCode', resCode)
			if check_sign and out_signs:
				client.check_res_sign(res_exp_sign)
			if res_time:
				add_check_point(case_id, client, res_time)
			if check1:
				add_check_point(case_id, client, check1)
			if Config.GLOBAL_DATA.get('能否直连数据库') is not None and Config.GLOBAL_DATA.get('能否直连数据库') == 'y':
				if zuh_charge:
					add_check_point(case_id, client, zuh_charge)
				if zdh_charges:
					add_check_point(case_id, client, zdh_charges)
				if zdh_counts:
					add_check_point(case_id, client, zdh_counts)
				if zuh_keys:
					add_check_point(case_id, client, zuh_keys)
				if zdh_keys:
					add_check_point(case_id, client, zdh_keys)
			if client.flag > 0:
				log(cid=case_id, result='fail')
			else:
				log(cid=case_id, result='pass')
		else:
			log(cid=case_id, desc=desc, result='skip', info='本次不运行该用例', error='是否运行列是n，本次不运行该用例')
			continue


create_report(duration=round(time.time() - start_time, 2), name='-'.join(names), start_time=start_time, infos=LOG_INFO)



