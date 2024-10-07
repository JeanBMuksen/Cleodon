# _*_ coding: utf-8 _*_
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys, os
from DTO import LogType
from conn_doccano_ia import CreateLog, InsertEmailReenvio, GetReenvioQueue, DeleteEmail, UpdateTentativasRestantesEmail

AMBIENTE = "prod_homol"
#AMBIENTE = "local"

def send_email(to, subject, message):
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = email_from
        msg['To'] =  to
        msg['Subject'] = subject 
        msg['X-Priority'] = "1"
        
        htmlBody = "<html><head></head><body> " + message + "</body></html>"
        emailBody = MIMEText(htmlBody, 'html', 'utf-8') # html body only works if called like this.. do not pass MIMEText direct to msg.attach(...).
        msg.attach(emailBody)
        text = msg.as_string()

        # Create a secure SSL context
        #context = ssl.create_default_context()
        
        #with smtplib.SMTP_SSL(smtp, port, context=context) as server:
        server = smtplib.SMTP(smtp, port)
        
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        server.login(email_from, password)

        smtp_ret = server.sendmail(email_from, to, text)

        str_ret = str(smtp_ret).strip()

        server.quit()
        server = None
        if smtp_ret != None and str_ret != "{}":
            raise Exception(str_ret)
        else:
            print("E-mail enviado com sucesso!")
    except Exception as e:
        if server != None:
            try:
                server.quit()
            except:
                pass

        raise e
    
def send_clean_s3_error(error_msg, notification_to):
    subject = ""
    message = ""
    try:
        subject = "Notificação - clean s3 error"
        message = "Olá! Ocorreu um erro: {0}".format(error_msg)
        send_email(notification_to, subject, message)
    except Exception as e:
        re_send_error = ""
        try:
            InsertEmailReenvio(notification_to, subject, message)
        except Exception as ex:
            re_send_error = " Também houve um erro ao gravar o e-mail na fila de reenvio. Mensagem: {0}".format(str(ex))
    
        msg_error = "clean_s3-send_clean_s3_error: Erro ao executar o serviço."
        if re_send_error != "":
            msg_error = msg_error + re_send_error
        #print(msg_error)
        CreateLog(msg_error, LogType.error_email.name, message=str(e))


# resend e-mail contingent process
def re_send_email():
    email_id = ""
    
    try:
        # get queue
        email_list = GetReenvioQueue()
        for email in email_list:
            email_id = email[0]
            tentativas_restantes = email[4]
            enviado = False
            try:
                if tentativas_restantes > 0:
                    # re_send
                    send_email(email[3], email[1], email[2])
                    
                    # control in case of error on delete..
                    enviado = True

                    # remove from queue
                    DeleteEmail(email_id)
                
            except Exception as exx:
                msg_error = "robo_dou-re_send_email: Erro ao reenviar e-mail."
                try:
                    if enviado == True:
                        # in case of error only on delete, try to set "tentativas_restantes" to zero.
                        UpdateTentativasRestantesEmail(email_id, 0)
                    elif tentativas_restantes > 0:
                        UpdateTentativasRestantesEmail(email_id, tentativas_restantes-1)
                except Exception as exc:
                    if enviado == True:
                        msg_error = msg_error + " O e-mail foi reenviado, porém não foi possível removê-lo da lista de reenvio e também não foi possível zerar o número de tentativas. Infelizmente ele será reenviado novamente até que seja possível removê-lo da lista ou zerar o número de tentativas. Motivo: " + str(exc)
                    else:
                        msg_error = msg_error + " Também houve um erro ao realizar update do número de tentativas (" + str(tentativas_restantes) + ") restantes para este envio. Motivo: " + str(exc)

                CreateLog(msg_error, LogType.error_email.name, message=str(exx), reference_name = "email_id", reference_id = email_id)
    except Exception as ex:
        CreateLog("robo_dou-re_send_email: Erro no processo de reenvio de e-mail.", LogType.error_email.name, message=str(ex), reference_name = "email_id", reference_id = email_id)
