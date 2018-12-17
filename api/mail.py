# coding=utf-8
import smtplib
from email.mime.text import MIMEText
from email.header import Header
 
def send_fpassword_reset_mail(receiver=None,username=None,set_password_link=None):
    if receiver and username and set_password_link:
        sender = 'Gengai@d-c.bid'
        receivers = []
        receivers.append(receiver)
        html = '''
        <p>嘿，{1}，<br>你可以<a href="{0}">点我</a>，或用浏览器打开下方链接来重置密码。</p>
        <p class="link">{0}</p>
        '''.format(set_password_link,username)
        message = MIMEText(html, 'html', 'utf-8')
        message['From'] = "{0}".format(sender)
        message['To'] =  "{0}".format(receiver)
        message['Subject'] = '重置梗概轻日记的密码'

        smtpObj = smtplib.SMTP()
        smtpObj.connect('smtp.ym.163.com', 25)
        smtpObj.login('gengai@d-c.bid','Abc19216811')
        smtpObj.sendmail(sender, [receiver], message.as_string())
        smtpObj.quit()

# send(receiver='imhcg@qq.com',username='imhcg',set_password_link='http://www.baidu.com')