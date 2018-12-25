# coding=utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header


def send_fpassword_reset_mail(receiver=None, username=None, set_password_link=None):
    print('开始发送邮件')
    sender = 'Gengai@d-c.bid'
    receivers = []
    receivers.append(receiver)
    html = '''
        <p>嘿，{1}，<br>你可以<a href="{0}">点我</a>，或用浏览器打开下方链接来重置密码。</p>
        <pre class="link">{0}</pre>
        '''.format(set_password_link, username)
    message = MIMEText(html, 'html', 'utf-8')
    message['From'] = "{0}".format(sender)
    message['To'] = "{0}".format(receiver)
    message['Subject'] = '重置梗概轻日记的密码'

    smtpObj = smtplib.SMTP()
    smtpObj.connect('smtp.ym.163.com', 25)
    smtpObj.login('gengai@d-c.bid', 'Abc19216811')
    smtpObj.sendmail(sender, [receiver], message.as_string())
    smtpObj.quit()
    print ('发送成功')
