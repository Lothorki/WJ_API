import time
from jinja2 import Template
from core.util import *
from core.email import *
import Config

def create_report(duration, start_time, infos, name):
	tmp = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
	with open('./report/template.html', encoding='utf-8', mode='r') as f:
		T = f.read()
	template = Template(T)
	# print(Config.GLOBAL_DATA)
	from_address = Config.GLOBAL_DATA.get('发件人')
	password = Config.GLOBAL_DATA.get('发件人密码')
	to_address = Config.GLOBAL_DATA.get('收件人').split(',')
	# 测试结果数据处理
	success = []
	fail = []
	skip = []
	res_times = analysis_time(infos=infos)
	for i in infos:
		if i['result'] == 'fail':
			fail.append(i)
		elif i['result'] == 'pass':
			success.append(i)
		elif i['result'] == 'skip':
			skip.append(i)

	text = '一共{testsRun}个用例，失败{failures}，通过{successes}， 跳过{skipped}'.format(
		testsRun=len(infos), successes=len(success), failures=len(fail), skipped=len(skip),
	)

	with open('./report/' + tmp + name + '.html', encoding='utf-8', mode='w') as f:
		f.write(template.render(
			html_report_name='接口测试报告',
			start_datetime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
			duration=duration,
			file_name=tmp + '.html',
			testsRun=len(infos),
			successes=len(success),
			failures=len(fail),
			skipped=len(skip),
			success_records=success,
			fail_records=fail,
			skip_records=skip,
			res_times=res_times))

		m = SendMail(username=from_address,
		             passwd=password,
		             recv=to_address,
		             title=tmp[0:8] + name + '测试结果',
		             content=text,
		             file='./report/' + tmp + name + '.html',
		             email_host='smtphm.qiye.163.com')
		m.send_mail()
		# send_email('./report/' + tmp + name + '.html', text)


