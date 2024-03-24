import smtplib
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('manojkumarmj991@gmail.com','hswnaojdrlkfrwsi')
    msg=EmailMessage()
    msg['From']='manojkumarmj991@gmail.com'
    msg['Subject']=subject
    msg['To']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()


