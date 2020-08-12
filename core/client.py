# coding=utf-8
import requests
import jsonpath
from requests_toolbelt.utils import dump
from core.util import *
import traceback
import Config as Config
import json
import time

LOG_INFO = []


def log(cid, result=None, desc=None, info=None, error=None, detail=None):
	for i in LOG_INFO:
		if i['id'] == cid:
			if result is not None:
				i['result'] = result
			if info is not None:
				i['log'].append(info)
			if error is not None:
				i['error'].append(error)
			if detail is not None:
				i['detail'].append(detail)
			break
	else:
		dic = {"id": cid, "desc": desc, "log": [], "error": [], "detail": []}
		if result is not None:
			dic['result'] = result
		if info is not None:
			dic['log'].append(info)
		if error is not None:
			dic['error'].append(error)
		if detail is not None:
			dic['detail'].append(detail)
		if desc is not None:
			dic["desc"] = desc
		LOG_INFO.append(dic)

def add_log(func):
	def wrapper(*arg, **kwargs):
		try:
			res = func(*arg, **kwargs)
		except:
			traceback.format_exc()
			arg[0].flag += 1
			# log(arg[0].case_id, error=traceback.format_exc().split('\n')[-2])
			log(arg[0].case_id, error=traceback.format_exc())
			return None
		log(arg[0].case_id, info=res)
		return res
	return wrapper


class Method:
	POST = 'post'
	GET = 'get'


class Body_Type:
	URL_ENCODED = 'url_encoded'
	JSON = 'json'
	XML = 'xml'
	FORM_DATA = 'form_data'


class Http:
	def __init__(self, url, case_id, method, body_type=None, timeout=3):
		if url.startswith('/'):
			self.url = 'http://' + Config.GLOBAL_DATA['ip'] + ':' + Config.GLOBAL_DATA['port'] + url
		else:
			self.url = url
		self.method = method
		self.body_type = body_type
		self.timeout = timeout
		self.headers = {}
		self.params = {}
		self.url_data = None
		self.body = {}
		self.case_id = case_id
		self.flag = 0
		self.__account = ''
		self.resp = None
		self.files = {}
		self.data = None

	def set_header(self, key, value):
		self.headers[key] = value

	def set_headers(self, headers_dict):
		if isinstance(headers_dict, dict):
			self.headers = headers_dict
		else:
			raise Exception('headers应为字典格式！')

	def set_params(self, params_dict):
		if isinstance(params_dict, dict):
			self.params = params_dict
		else:
			raise Exception('params应为字典格式！')

	def set_url_data(self, url_data):
		self.url_data = url_data

	def set_body(self, body_dict):
		if isinstance(body_dict, dict):
			self.body = body_dict
		else:
			raise Exception('body应为字典格式！')

	def set_files(self, files_dict):
		if isinstance(files_dict, dict):
			self.files = files_dict

	def set_account(self, account):
		self.__account = account


	def send(self):
		try:
			if self.method == 'get':
				if self.body_type == 'url参数':
					try:
						self.url = self.url + '?' + self.url_data
						self.resp = requests.get(url=self.url,
						                          headers=self.headers,
						                          timeout=self.timeout)
					except Exception as e:
						print(e)
				else:
					try:
						self.resp = requests.get(url=self.url,
									 params=self.params,
									 timeout=self.timeout)
					except Exception as e:
						print(e)
			elif self.method == 'post':
				if self.body_type == 'url_encoded':
					self.set_header('Content-Type', 'application/x-www-form-urlencoded')
					try:
						self.resp = requests.post(url=self.url,
									  headers = self.headers,
									  data = self.body,
									  timeout = self.timeout)
					except Exception as e:
						print(e)
				elif self.body_type == 'json':
					self.set_header('Content-Type', 'application/json')
					try:
						self.resp = requests.post(url=self.url,
									  headers = self.headers,
									  json= self.body,
									  timeout = self.timeout)
					except Exception as e:
						print(e)
				elif self.body_type == 'xml':
					self.set_header('Content-Type', 'text/xml')
					self.body = self.body.get('xml')
					try:
						if self.body:
							self.resp = requests.post(url=self.url,
										  headers = self.headers,
										  data = self.body,
										  timeout = self.timeout)
						else:
							raise Exception("xml格式不正确，应为{'xml':'''xxxxxxxxx'''}")
					except Exception as e:
						print(e)
				elif self.body_type == 'form_data':
					formed_data = {}
					if self.files:
						for k, v in self.files.items():
							formed_data[k] = open(v, 'rb')
					if self.body:
						for k, v in self.body.items():
							formed_data[k] = (None, v)
					self.body = formed_data
					try:
						self.resp = requests.post(url=self.url,
							  headers = self.headers,
							  files = self.body,
							  timeout = self.timeout)
					except Exception as e:
						print(e)
				else:
					raise Exception('请求正文格式不支持')
			else:
				raise Exception('请求方式错误，只支持get和post')
		except:
			log(cid=self.case_id, error='请求发送失败:\n' + traceback.format_exc())
		finally:
			log(cid=self.case_id, detail='请求地址:' + self.url)
			log(cid=self.case_id, detail='请求方法:' + self.method)
			log(cid=self.case_id, detail='请求头:' + json.dumps(self.headers))
			log(cid=self.case_id, detail='请求正文:' + json.dumps(self.body))
			if self.url_data is not None:
				log(cid=self.case_id, detail='请求url参数:' + self.url_data)
			else:
				log(cid=self.case_id, detail='请求url参数:' + json.dumps(self.params))
			if self.resp:
				log(cid=self.case_id, detail='响应状态码:' + str(self.resp.status_code))
				log(cid=self.case_id, detail='响应正文:' + json.dumps(self.response_text, ensure_ascii=False))
				log(cid=self.case_id, detail='响应时间:' + str(self.response_time))
			else:
				log(cid=self.case_id, detail='响应状态码:' + 'None')
				log(cid=self.case_id, detail='响应正文:' + 'None')
				log(cid=self.case_id, detail='响应时间:' + '0')
			if self.cookies is not None:
				log(cid=self.case_id, detail='cookie:' + json.dumps(requests.utils.dict_from_cookiejar(self.cookies)))

	@property
	def get_detail_info(self):
		self.data = dump.dump_all(self.resp)
		return self.data.decode('utf-8')

	@property
	def cookies(self):
		if self.resp is not None:
			return self.resp.cookies
		else:
			print('响应内容为空，cookies获取失败')
			return None

	@property
	def response_text(self):
		if self.resp:
			return self.resp.text
		else:
			return None

	@property
	def response_status_code(self):
		if self.resp:
			return self.resp.status_code
		else:
			return None

	@property
	def response_headers(self):
		if self.resp:
			return self.resp.headers
		else:
			return None

	@property
	def response_cookies(self):
		if self.resp:
			return self.resp.cookies
		else:
			return None

	@property
	def response_time(self):
		if self.resp:
			return round(self.resp.elapsed.microseconds/1000)
		else:
			return None

	@property
	def response_jsonObj(self):
		if self.resp:
			try:
				return self.resp.json()
			except:
				raise Exception('响应体不是JSON格式')
		else:
			return None

	@property
	def tid(self):
		res = self.get_response_json_value('$.tid')
		if res is not None:
			return res
		else:
			raise Exception('响应中没有tid')



	def get_response_json_value(self, json_path):
		res = None
		if not json_path.startswith('$.'):
			json_path = '$.' + json_path
		if self.resp:
			try:
				res = jsonpath.jsonpath(self.response_jsonObj, json_path)[0]
				return res
			except:
				raise Exception('响应体不是JSON格式 或没找到{json_path}字段'.format(json_path=json_path))
			finally:
				return res
		else:
			return None

# 检查点
	# 响应状态码
	@add_log
	def check_status_code(self, code):
		assert self.resp.status_code == code,\
			'响应状态码不正确，期望：【%d】，实际：【%s】' % (code, self.response_status_code)
		return '响应状态码验证通过'

	# 验证关键信息
	@add_log
	def check_response_contains(self, keywords, reverse=False):
		if reverse == False:
			key_words = ''
			if isinstance(keywords, list):
				key_words = ':'.join(keywords)
			elif isinstance(keywords, str):
				key_words = keywords
			assert key_words in self.response_text, \
				'关键信息验证失败，期望：包含【%s】，实际：未包含' % key_words
			return '关键信息验证通过'
		else:
			assert keywords not in self.response_text, \
				'关键信息验证失败，期望：不包含【%s】，实际：包含' % keywords
			return '关键信息验证通过'

	@add_log
	def check_response_json_node_exists(self, json_path, reverse=False):
		if reverse == False:
			assert jsonpath.jsonpath(self.response_jsonObj, json_path),\
				'Json字段验证失败，期望：包含【%s】，实际：未包含' % json_path
			return 'Json字段验证通过'
		else:
			assert jsonpath.jsonpath(self.response_jsonObj, json_path) == False, \
				'Json字段验证失败，期望：不包含【%s】，实际：包含' % json_path
			return 'Json字段验证通过'

	@add_log
	def check_response_json_value(self, json_path, exp_value):
		# result = jsonpath.jsonpath(self.response_jsonObj, json_path)[0]
		result = self.get_response_json_value(json_path)
		# print(json_path, result)
		b = ''
		if result is not None:
			if isinstance(exp_value, float):
				b = int(exp_value)
			else:
				b = str(exp_value)
			assert str(result) == str(b), \
				'Json字段值验证失败，jsonpath【%s】，期望：【%s】，实际：【%s】' % (json_path, b, result)
			r = 'Json字段值验证通过'+ json_path
			return r

	@add_log
	def check_response_time(self, exp_max_time):
		act_time = self.response_time
		assert act_time <= int(exp_max_time), \
			'响应时间验证失败，期望：<【%.1f毫秒】，实际：【%.1f毫秒】' % (exp_max_time, act_time)
		return '响应时间验证通过'

	@add_log
	def check_res_equal(self, text):
		assert self.res_text == text, '检查失败，实际结果【{a}】，预期结果【{b}】'.format(
			a=self.res_text, b=text
		)
		return '响应文本检查成功'


	@add_log
	def check_res_sign(self, exp):
		act = self.get_response_json_value('sign')
		if act is not None:
			assert act == exp, '响应签名验证失败，实际结果是【{act}】,预期是【{exp}】'.format(
				act=act, exp=exp
			)
		return '响应签名验证成功'


	@add_log
	def check_zuh_charge(self, b):
		times = [0, 1, 2, 3]
		for i in times:
			db_connect = get_dbconnetcion()
			cursor = db_connect.cursor()
			sql = "select charge from pccredit.zx_user_history where tid = '{ttt}'".format(ttt=self.tid)
			try:
				cursor.execute(sql)
				a = cursor.fetchall()[0][0]
				assert str(a) == str(b), 'zuh计费校验失败，实际结果是【{a}】,预期是【{b}】'.format(
					b=b, a=a)
				return 'zuh计费验证通过'
			except IndexError:
				if i == times[-1]:
					raise Exception('没找到{tid}相关的记录,zuh计费校验失败'.format(ttt=self.tid))
				else:
					time.sleep(0.8)
					continue
			finally:
				cursor.close()
				db_connect.close()



	@add_log
	def check_zdh_charge(self, ds_name, ds_type, b):
		times = [0, 1, 2, 3]
		for i in times:
			db_connect = get_dbconnetcion()
			cursor = db_connect.cursor()
			sql = "select charge from pccredit.zx_ds_history where ds_name = '{ds_name}' " \
			      "and type = {type} and tid = '{ttt}'".format(
				ttt=self.tid, ds_name=ds_name, type=ds_type)
			try:
				cursor.execute(sql)
				a = cursor.fetchall()[0][0]
				assert str(a) == str(b), 'zdh计费校验失败，数据源【{ds_name}】，ds_type【{ds_type}】' \
				                         '计费实际结果是【{a}】,预期是【{b}】'.format(
					b=b, a=a, ds_name=ds_name, ds_type=ds_type)
				return 'zdh数据源【{ds_name}】，ds_type【{ds_type}】计费验证通过'.format(
					ds_name=ds_name, ds_type=ds_type)
			except IndexError:
				if i == times[-1]:
					raise Exception('没找到{tid}相关的记录,zdh数据源【{ds_name}】，ds_type【{ds_type}】计费校验失败'.format(
						ttt=self.tid, ds_name=ds_name, type=ds_type))
				else:
					time.sleep(0.8)
					continue
			finally:
				cursor.close()
				db_connect.close()


	@add_log
	def check_ds_count(self, count):
		times = [0, 1, 2, 3]
		for i in times:
			db_connect = get_dbconnetcion()
			cursor = db_connect.cursor()
			sql = "select count(*) from pccredit.zx_ds_history where tid = '{ttt}'".format(ttt=self.tid)
			try:
				cursor.execute(sql)
				a = cursor.fetchall()[0][0]
				assert str(a) == str(count), 'zdh数据条数校验失败，实际结果是【{a}】,预期是【{count}】'.format(
					count=count, a=a)
				return 'zdh数据条数验证通过'
			except IndexError:
				if i == times[-1]:
					raise Exception('没找到{tid}相关的记录,zdh数据条数校验失败'.format(
						ttt=self.tid))
				else:
					time.sleep(0.8)
					continue
			finally:
				cursor.close()
				db_connect.close()

	@add_log
	def check_zuh_not_null(self, key):
		times = [0, 1, 2, 3]
		for i in times:
			db_connect = get_dbconnetcion()
			cursor = db_connect.cursor()
			sql = "select {key} from pccredit.zx_user_history where tid = '{ttt}'".format(ttt=self.tid, key=key)
			try:
				cursor.execute(sql)
				a = cursor.fetchall()[0][0]
				assert a is not None, 'zuh字段{key}校验失败，实际结果是空,预期非空'.format(
					key=key)
				assert len(str(a)) > 0, 'zuh字段{key}校验失败，实际结果是空,预期非空'.format(
					key=key)
				return 'zuh字段{key}校验通过'.format(key=key)
			except IndexError:
				if i == times[-1]:
					raise Exception('没找到{tid}相关的记录,zuh字段{key}字段校验失败'.format(ttt=self.tid, key=key))
				else:
					time.sleep(0.8)
					continue
			finally:
				cursor.close()
				db_connect.close()

	@add_log
	def check_zdh_not_null(self, key, ds_name, ds_type):
		times = [0, 1, 2, 3]
		for i in times:
			db_connect = get_dbconnetcion()
			cursor = db_connect.cursor()
			sql = "select {key} from pccredit.zx_ds_history where 1=1 and tid = '{ttt}' and ds_name = '{ds_name}' " \
			      "and type = '{ds_type}' ".format(
				ttt=self.tid, key=key, ds_name=ds_name, ds_type=ds_type)
			try:
				cursor.execute(sql)
				a = cursor.fetchall()[0][0]
				assert a is not None, 'zdh-{ds_name}-{ds_type}字段{key}校验失败，实际结果是空,预期非空'.format(
					key=key, ds_name=ds_name, ds_type=ds_type)
				assert len(str(a)) > 0, 'zdh-{ds_name}-{ds_type}字段{key}校验失败，实际结果是空,预期非空'.format(
					key=key, ds_name=ds_name, ds_type=ds_type)
				return 'zdh-{ds_name}-{ds_type}字段{key}校验通过'.format(key=key, ds_name=ds_name, ds_type=ds_type)
			except IndexError:
				if i == times[-1]:
					raise Exception('没找到{tid}相关的记录,zdh字段{key}字段校验失败'.format(
						ttt=self.tid, key=key,
						ds_name=ds_name, ds_type=ds_type))
				else:
					time.sleep(0.8)
					continue
			finally:
				cursor.close()
				db_connect.close()


