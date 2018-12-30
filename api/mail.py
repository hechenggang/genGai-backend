# coding=utf-8
import sys
sys.path.append('..')
import config

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr,parseaddr


def send(user=None, content=None, subject=None):
    # print('开始发送邮件')
    # print(user,content,subject)
    # print((Header(config.app['name']),config.mail_config['username']))
    message = MIMEText(content, 'html', 'utf-8')
    message['From'] = _formataddr('{} <{}>'.format(config.app['name'],config.mail_config['username']))
    message['To'] = _formataddr('{} <{}>'.format(user['name'],user['mail']))
    message['Subject'] = Header(subject)
    # print (message.as_string())
    smtp = smtplib.SMTP_SSL(host=config.mail_config['server'])
    smtp.connect(config.mail_config['server'], config.mail_config['port'])
    smtp.login(config.mail_config['username'], config.mail_config['password'])
    smtp.sendmail(config.mail_config['username'], [user['mail']], message.as_string())
    smtp.quit()
    # print ('发送成功')

def _header(name):
    return Header(name,'utf-8').encode()

def _formataddr(string):
    name, addr = parseaddr(string)
    return formataddr((_header(name),addr))