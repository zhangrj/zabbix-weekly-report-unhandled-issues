#!/usr/bin/python
# coding=utf-8

import smtplib
from email.header import Header
from email.mime.text import MIMEText

from pyzabbix import ZabbixAPI

# The hostname at which the Zabbix web interface is available
ZABBIX_SERVER = 'http://192.168.128.181/zabbix/'
zapi = ZabbixAPI(ZABBIX_SERVER)
# Login to the Zabbix API
zapi.login('Admin', 'zabbix@ngcc')

# mail information
server = "192.168.131.208"
port = 25
user = "zabbix@jiangsucallcenter.com.cn"
password = "7C39Sn5VUM"
sender = "zabbix@jiangsucallcenter.com.cn"
receivers = ["2073665763@qq.com","18260067809@163.com"]

def get_latest_data_by_itemid(itemid):
	item_info = zapi.item.get(itemids=itemid)
	'''
	data_type = item_info[0][u'value_type']
	history_info = zapi.history.get(history=int(data_type),
									itemids=itemid,
									sortfield="clock",
									sortorder="DESC",
									limit=1)
	value = history_info[0][u'value']
	value_unit = history_info[0][u'units']
	'''
	value = item_info[0][u'lastvalue']
	value_unit = item_info[0][u'units']
	return value + value_unit

# Get a list of all issues (AKA tripped triggers)
def get_issues():
	# only_true : 仅返回最近处于故障状态的触发器
	# skipDependent : 依赖其他触发器的触发器处在故障状态时就跳过
	# monitored : 仅返回所属被监控主机的已启用触发器，并包含已启用的监控项。
	# active : 仅返回所属被监控主机的已启用触发器
	# min_severity : 仅返回严重级别大于或等于指定严重级别的触发器，2表示严重级别大于等于警告
	triggers = zapi.trigger.get(only_true=1,
								skipDependent=1,
								monitored=1,
								active=1,
								min_severity=2,
								output='extend',
								selectFunctions = "extend",
								expandDescription=1,
								selectHosts=['host']
								)
	issues = []
	for trigger in triggers:
		issue = {}
		issue['host_ip'] = trigger[u'hosts'][0][u'host'].encode("utf-8")
		issue['host_description'] = zapi.host.get(hostids=trigger[u'hosts'][0][u'hostid'])[0][u'name'].encode("utf-8")
		issue['issue'] = trigger[u'description'].encode("utf-8")
		itemid = trigger[u'functions'][0][u'itemid'].encode("utf-8")
		issue['item_value'] = get_latest_data_by_itemid(itemid).encode("utf-8")
		issues.append(issue)
	print issues
	return issues


def send_email(server, port, user, password, sender, receivers, content):
	smtpObj = smtplib.SMTP()
	mail_msg = '''
	<table border="1">
	<tr>
  		<td>序号</td>
  		<td>主机IP</td>
  		<td>主机描述</td>
  		<td>未处理告警</td>
  		<td>当前数据</td>
	</tr>'''

	i = 0
	for issue in content:
		i += 1 
		mail_msg += "<tr>"
		mail_msg += "<td>" + str(i) + "</td>"
		mail_msg += "<td>" + issue['host_ip'] + "</td>"
		mail_msg += "<td>" + issue['host_description'] + "</td>"
		mail_msg += "<td>" + issue['issue'] + "</td>"
		mail_msg += "<td>" + issue['item_value'] + "</td>"
		mail_msg += "</tr>"
	mail_msg += "</table>"

	message = MIMEText(mail_msg,'html','utf-8')
	message['To'] = Header(','.join(receivers))
	subject = '本周未处理告警'
	message['Subject'] = Header(subject, 'utf-8')
	smtpObj.connect(server, port)
	smtpObj.login(user, password)
	smtpObj.sendmail(sender, receivers, message.as_string())

if __name__ == "__main__":
	current_issues = get_issues()
	send_email(server, port, user, password, sender, receivers, current_issues)