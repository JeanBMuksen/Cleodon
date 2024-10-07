# _*_ coding: utf-8 _*_
import MySQLdb
import os.path
import mysql.connector
from DTO import SentenceAnnotation
from DTO import LogType
from datetime import datetime


AMBIENTE_LOG_PATH = "/usr/spacy/leitor/static/log/log.txt"

def DbConnect():
    return mysql.connector.connect(user="", password="", host='', database='', port="")

#in case of error in process publication, rollback database to keep it able to retry processment
def RollBackPublicationProcess(publication_id, rollback_motive, context = None):    
    try: 
        if context != None:
            cnx = context
        else:
            cnx = DbConnect()

        cursor = cnx.cursor()

        #rollback annotations
        query = "delete annot from api_sequenceannotation as annot inner join api_document as doc on annot.document_id = doc.id where doc.publication_id = " + str(publication_id) + "; "

        #rollback sentences
        query = query + " delete from api_document where publication_id = " + str(publication_id) + "; "

        #rollback publication
        query = query + " update api_publication set active = 1, processed = 0, pdf_has_annotation = null where id = " + str(publication_id) + "; "
        
        for result in cursor.execute(query, multi=True):
            pass
        
        cnx.commit()    
        cursor.close() 
        
        if context == None:
            cnx.close()

        CreateLog("robo_dou-ProcessPublication-RollBackPublicationProcess", LogType.success.name, message="Rollback realizado com sucesso!", reference_name="publication_id", reference_id=publication_id, context=context)
    except Exception as eeexce:
        msg_rollback_error = str(eeexce)
        full_msg = "Rollback error: {0} \n\n\n parent error: {1}".format(msg_rollback_error, rollback_motive)
        CreateLog("robo_dou-ProcessPublication-RollBackPublicationProcess: Erro ao realizar rollback da publicação", LogType.error.name, message=full_msg, reference_name="publication_id", reference_id=publication_id, context=context)

def CreateLog(description, log_type, message = None, reference_name = None, reference_id = None, context = None):
    id = None
    try:
        if context != None:
            cnx = context
        else:
            cnx = DbConnect()

        cursor = cnx.cursor()

        query = "INSERT INTO api_log (create_date, description, log_type"
        if message != None:
            query += ", message"
        if reference_name != None:
            query += ", reference_name"
        if reference_id != None:
            query += ", reference_id"
            
        query += ") VALUES (now(), '" + description.replace("\'", "\'\'") + "', '" + log_type + "'"
        
        if message != None:
            query += ", '" + message.replace("\'", "\'\'") + "'"
        if reference_name != None:
            query += ", '" + reference_name + "'"
        if reference_id != None:
            query += ", " + str(reference_id) 

        query += ")"

        cursor.execute(query)
        cnx.commit()
        id = cursor.lastrowid
        cursor.close() 
        
        if context == None:
            cnx.close()

        return id    
    except Exception as eex:
        file_log = None
        if os.path.exists(AMBIENTE_LOG_PATH):
            file_log = open(AMBIENTE_LOG_PATH, "a", encoding='utf8')
        else:
            file_log = open(AMBIENTE_LOG_PATH, "w", encoding='utf8')

        if file_log != None:            
            file_log.write("------------------------------------------------------------------------")
            file_log.write("\nErro ao salvar o log abaixo na tabela: api_log\n")
            
            file_log.write("\nData/Hora: " + str(datetime.today()))
            file_log.write("\nlog_type: " + str(log_type))
            file_log.write("\ndescription: " + str(description))
            file_log.write("\nmessage: " + str(message))
            file_log.write("\nreference_name: " + str(reference_name))
            file_log.write("\nreference_id: " + str(reference_id))

            file_log.write("\nSTACK TRACE:\n")
            file_log.write(str(eex) + "\n")

            file_log.close()
        return id

def GetSentenceAnnotation(isTrainning, project_id, perfil_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("  SELECT document.id AS document_id, document.text as document_text, annotation.start_offset, annotation.end_offset, label.id as label_id, label.text as label_text " +
            "   FROM api_document AS document " +
            "   LEFT JOIN api_sequenceannotation AS annotation ON document.id = annotation.document_id  " +
            "   LEFT JOIN api_label AS label ON label.id = annotation.label_id  " +
            "   LEFT JOIN api_perfillabel as perfil ON perfil.label_id = annotation.label_id" +
            "   WHERE document.project_id = '" + str(project_id) + "' AND perfil.perfil_id = '" + str(perfil_id) + "' and label.project_id = '" + str(project_id) + "' ")

    if(isTrainning == True):
        query += (" AND document.trainning = true ")

    query += (" GROUP BY document_text, start_offset, end_offset, label_id, label_text ")

    cursor.execute(query)
    sentence_annotation_list = []
    sentence_annotation = []
    for (document_id, document_text, start_offset, end_offset, label_id, label_text) in cursor:
        sentence_annotation = SentenceAnnotation()
        sentence_annotation.document_id = document_id
        sentence_annotation.document_text = document_text
        sentence_annotation.start_offset = start_offset
        sentence_annotation.end_offset = end_offset
        sentence_annotation.label_id = label_id
        sentence_annotation.label_text = label_text
        sentence_annotation_list.append(sentence_annotation)

    cursor.close() 

    if context == None:
        cnx.close()

    return sentence_annotation_list

# método de consulta de fila de publicação a ser processada.
def GetPublicationQueueByProject(project_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("  SELECT pub.id, pub.file_path, pub.text, pub.perfil_id " +
            "   FROM api_publication pub " +
            "   INNER JOIN api_perfil perfil on perfil.id = pub.perfil_id " + 
            "   WHERE pub.project_id = '" + str(project_id) + "' and pub.processed = false and pub.active = true and perfil.active = true")

    cursor.execute(query)
    publication_list = []
    for (id, file_path, text, perfil_id) in cursor:
        publication_list.append((id, file_path, text, perfil_id))

    cursor.close() 
    if context == None:
        cnx.close()

    return publication_list
    
def UpdateProcessedPublication(publication_id, pdf_has_annotation, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("UPDATE api_publication set active = true, processed = true, pdf_has_annotation = " + str(pdf_has_annotation).lower() + " WHERE id = " + str(publication_id))
    cursor.execute(query)
    cnx.commit()
    cursor.close() 
    
    if context == None:
        cnx.close()

def ActivatePublication(publication_id, active, context = None):
    try:
        if context != None:
            cnx = context
        else:
            cnx = DbConnect()

        cursor = cnx.cursor()
        query = ("UPDATE api_publication set active = " + str(active).lower() + " WHERE id = " + str(publication_id))
        cursor.execute(query)
        cnx.commit()
        cursor.close() 
        
        if context == None:
            cnx.close()
    except Exception as exc:
        CreateLog("robo_dou-ActivatePublication: Erro ao ativar publicação!", LogType.error.name, message=str(exc), reference_name="publication_id", reference_id=publication_id)        

def RollbackSentence(sentence_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("delete from api_document where id = " + str(sentence_id))
    cursor.execute(query)
    cnx.commit()
    cursor.close() 
    
    if context == None:
        cnx.close()


def InsertSentence(text, project_id, page, publication_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    id = None
    cursor = cnx.cursor()
    
    if text != None:
        text = text.replace("\'", "\'\'")

    query = ("INSERT INTO api_document (text, meta, project_id, publication_id, page, created_at, updated_at, trainning) VALUES ('" + text + "', '{}', '" + str(project_id) + "', '" + str(publication_id) + "', '" + str(page) + "', now(), now(), false)")
    cursor.execute(query)
    cnx.commit()
    id = cursor.lastrowid
    cursor.close() 
    
    if context == None:
        cnx.close()
    
    return id

def InsertSentenceEntity(user_id, document_id, label_id, start_offset, end_offset, context = None, cursor = None, parentCommit = False):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    if cursor == None:
        cursor = cnx.cursor()

    query = ("INSERT INTO api_sequenceannotation (user_id, document_id, label_id, start_offset, end_offset, created_at, updated_at, prob, manual) VALUES ('" + str(user_id) + "', '" + str(document_id) + "', '" + str(label_id) + "', '" + str(start_offset) + "', '" + str(end_offset) + "', now(), now(), 0, 0)")
    cursor.execute(query)

    #if parentCommit == True then commit will be done in parent level
    if parentCommit == False:
        cnx.commit()
        cursor.close() 
    
    if context == None:
        cnx.close()

def GetEntityId(text, project_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()
        
    cursor = cnx.cursor()
    query = ("SELECT id, text FROM api_label WHERE project_id = '" + str(project_id) + "' and text = '" + text + "' limit 1")
    cursor.execute(query)
    entity_id = None
    for (id, text) in cursor:
        entity_id = id
    cursor.close() 
    
    if context == None:
        cnx.close()

    return entity_id
    
def GetEntityIdList(project_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()
        
    cursor = cnx.cursor()
    query = ("SELECT id, text FROM api_label WHERE project_id = '" + str(project_id) + "'")
    cursor.execute(query)
    entity_data = []
    for (id, text) in cursor:
        entity_data.append((id, text))
    cursor.close() 
    
    if context == None:
        cnx.close()

    return entity_data

def InsertEntity(text, project_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    id = None
    cursor = cnx.cursor()
    
    if text != None:
        text = text.replace("\'", "\'\'")

    query = ("INSERT INTO api_label (text, project_id, prefix_key, suffix_key, background_color, text_color, created_at, updated_at) VALUES ('" + text + "', '" + str(project_id) + "', '', '', '#209cee', '#ffffff', now(), now())")
    cursor.execute(query)
    cnx.commit()
    id = cursor.lastrowid
    cursor.close() 
    
    if context == None:
        cnx.close()

    return id

def InsertEmailReenvio(notification_to, subject, message, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    id = None
    cursor = cnx.cursor()
        
    if notification_to != None:
        notification_to = notification_to.replace("\'", "\'\'")
    
    if subject != None:
        subject = subject.replace("\'", "\'\'")

    if message != None:
        message = message.replace("\'", "\'\'")

    query = ("INSERT INTO api_email (create_date, subject, message, notification_to, tentativas_restantes) VALUES (now(), '" + subject + "', '" + message + "', '" + notification_to + "', 3 )")
    cursor.execute(query)
    cnx.commit()
    id = cursor.lastrowid
    cursor.close() 
    
    if context == None:
        cnx.close()

    return id

def GetReenvioQueue(context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("select id, subject, message, notification_to, IFNULL(tentativas_restantes, 0) as tentativas_restantes from api_email where tentativas_restantes > 0 order by tentativas_restantes desc limit 5") # order by tentativas_restantes desc para dar prioridade aos e-mails que ainda não foram reenviados.

    cursor.execute(query)
    email_list = []
    for (id, subject, message, notification_to, tentativas_restantes) in cursor:
        email_list.append((id, subject, message, notification_to, tentativas_restantes))

    cursor.close() 
    if context == None:
        cnx.close()

    return email_list

def DeleteEmail(email_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("delete from api_email where id = " + str(email_id))
    cursor.execute(query)
    cnx.commit()
    cursor.close() 
    
    if context == None:
        cnx.close()

def UpdateTentativasRestantesEmail(email_id, tentativas_restantes, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("update api_email set tentativas_restantes = " + str(tentativas_restantes) + " where id = " + str(email_id))
    cursor.execute(query)
    cnx.commit()
    cursor.close() 
    
    if context == None:
        cnx.close()

# método de consulta de fila de publicação a ser processada no clean_s3 job.
def GetPublicationList(project_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("  SELECT id, file_path, create_date " +
            "   FROM api_publication " +
            "   WHERE project_id = '"+ str(project_id) +"' AND api_publication.id NOT IN (1)")

    cursor.execute(query)
    publication_list_bd = []
    for (id, file_path, create_date) in cursor:
        publication_list_bd.append((id, file_path, create_date))

    cursor.close() 
    if context == None:
        cnx.close()

    return publication_list_bd

# delete publication for clean_s3 job
def DeletePublication(publication_id, context = None):    
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()

    #delete annotations
    query = "delete annot from api_sequenceannotation as annot inner join api_document as doc on annot.document_id = doc.id where doc.publication_id = " + str(publication_id) + "; "

    #delete sentences
    query = query + " delete from api_document where publication_id = " + str(publication_id) + "; "

    #delete publication
    query = query + " delete from api_publication where id = " + str(publication_id) + "; "

    for result in cursor.execute(query, multi=True):
        pass
    
    cnx.commit()    
    cursor.close() 
    
    if context == None:
        cnx.close()

# Get Black List to clean Text
def GetBlackList(context = None):

    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("select text from api_blacklist") # Seleciona objetos da blacklist.

    cursor.execute(query)
    black_list = []
    for (text) in cursor:
        black_list.append(text)

    cursor.close() 
    if context == None:
        cnx.close()

    return black_list