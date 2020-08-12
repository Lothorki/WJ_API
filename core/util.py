import pymysql
import xlrd
import hashlib
import Config as Config
import re

def get_gloable_data(name):
	data = {}
	workbook = xlrd.open_workbook('./cases/testcase.xls')
	try:
		sheet = workbook.sheet_by_name(name)
		for i in range(1, sheet.nrows):
			key = sheet.row_values(i)[0]
			value = sheet.row_values(i)[1]
			data[key] = value
		return data
	except xlrd.biffh.XLRDError:
		raise Exception('sheet页不存在')

def get_data_from_sheet(name):
	data = []
	workbook = xlrd.open_workbook('./cases/testcase.xls')
	try:
		sheet = workbook.sheet_by_name(name)
		headers = sheet.row_values(0)
		for i in range(1, sheet.nrows):
			dic = {}
			for index, value in enumerate(sheet.row_values(i)):
				dic[headers[index]] = value
			data.append(dic)
		return data
	except xlrd.biffh.XLRDError:
		raise Exception('sheet页不存在')


def get_dbconnetcion():
	host = Config.DB_PARAMS.get('地址')
	port = Config.DB_PARAMS.get('端口')
	user = Config.DB_PARAMS.get('账号')
	password = Config.DB_PARAMS.get('密码')

	return pymysql.connect(host=host, port=int(port), user=user, password=password)

def update_mock(info):
	l = info.split('\n')
	if len(l) < 2:
		raise Exception('数据源mock格式错误')
	else:
		url = l[0].split(':')[-1]
		respond = ':'.join(l[1].split(':')[1:])
		update_mock_respond(url, respond)

def update_mock_respond(url, respond):
	db_connection = get_dbconnetcion()
	cursor = db_connection.cursor()
	query = "update {table} set respond = '{respond}' where url = '{url}'".format(
		table=Config.DB_PARAMS.get('mock_table'), respond=respond, url=url
	)
	cursor.execute(query)
	db_connection.commit()
	cursor.close()
	db_connection.close()



def get_sign(param_dict, sign_params, account=None):
	if isinstance(param_dict, dict):
		sign_dict = {}
		p_keys = list(param_dict.keys())
		params = []
		for s in sign_params:
			params.append(s)
		for s in sign_params:
			if s in p_keys:
				params.remove(s)
				sign_dict[s] = param_dict[s]
		for k in p_keys:
			if isinstance(param_dict[k], dict):
				ky = list(param_dict[k].keys())
				for p in params:
					if p in ky:
						sign_dict[p] = param_dict[k][p]
		return sign(sign_dict, account)
	else:
		print('参数类型需要是字典')


def sign(dic, account=None):
	li = []
	for k, v in dic.items():
		li.append(k + str(v))
	para_str = sorted(li)
	signbase = ''
	for i in para_str:
		signbase += i

	sign = ''
	if account is None:
		sign = signbase + Config.ACCOUNT[dic.get('account')]
	else:
		sign = signbase + Config.ACCOUNT.get(account, '')
	hl = hashlib.md5()
	hl.update(sign.encode(encoding='utf-8'))
	sign2 = hl.hexdigest()
	return sign2.upper()



def add_check_point(cid, client, checks):
	check_list = checks.split('\n')
	for check in check_list:
		checks = check.split(',')
		if checks[0] == '节点':
			client.check_response_json_value(checks[1], checks[2])
		elif checks[0] == '时间':
			client.check_response_time(int(checks[1]))
		elif checks[0] == 'zdh记录条数':
			client.check_ds_count(checks[1])
		elif checks[0] == 'zuh计费':
			client.check_zuh_charge(checks[1])
		elif checks[0] == 'zdh计费':
			client.check_zdh_charge(checks[1].split('/')[0],
			                                       checks[1].split('/')[1],
			                                       checks[-1])
		elif checks[0] == 'zuh字段':
			if len(checks) > 2:
				for c in checks[1:]:
					client.check_zuh_not_null(c)
			else:
				client.check_zuh_not_null(checks[1])
		elif checks[0] == 'zdh字段':
			if len(checks) > 3:
				for c in checks[2:]:
					client.check_zdh_not_null(c, ds_name=checks[1].split('/')[0],
					                                         ds_type=checks[1].split('/')[1])
			else:
				client.check_zdh_not_null(checks[2], ds_name=checks[1].split('/')[0],
				                          ds_type=checks[1].split('/')[1])
		else:
			# log(cid=cid, info='{check}检查点无效'.format(check=checks))
			print(cid, checks, '检查点无效')


def replace_var(source):
	variable_regexp = r"\${([\w_]+)"
	result = re.findall(variable_regexp, source)
	if result:
		for r in result:
			if Config.GLOBAL_DATA.get(r) is not None:
				source = source.replace('${' + r + '}', Config.GLOBAL_DATA.get(r))

	return source


def get_res_times(infos):
	times = []
	if isinstance(infos, list):
		for i in infos:
			details = i.get('detail')
			if details is not None and len(details) > 0:
				for d in details:
					if d.startswith('响应时间'):
						times.append(int(d.split(':')[1]))
	return times



def analysis_time(infos):
	times = get_res_times(infos)
	a = 0
	b = 0
	c = 0
	d = 0
	e = 0
	f = 0
	if isinstance(times, list) and len(times) > 0:
		for t in times:
			if isinstance(t, int):
				if t <= 50:
					a += 1
				elif 50 < t <= 100:
					b += 1
				elif 100 < t <= 200:
					c += 1
				elif 200 < t <= 500:
					d += 1
				elif 500 < t <= 1000:
					e += 1
				elif t > 1000:
					f += 1
		return [a, b, c, d, e, f]
	else:
		return None