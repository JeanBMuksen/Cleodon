# _*_ coding: utf-8 _*_
import MySQLdb
import mysql.connector
from .DTO import SentenceAnnotation, Publications

def DbConnect():
    return mysql.connector.connect(user="", password="", host='', database='', port="")

def InsertSentence(text, project_id, page, publication_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    id = None
    cursor = cnx.cursor()
    query = ("INSERT INTO api_document (text, meta, project_id, publication_id, page, created_at, updated_at, trainning) VALUES ('" + text + "', '{}', '" + str(project_id) + "', '" + str(publication_id) + "', '" + str(page) + "', now(), now(), false)")
    cursor.execute(query)
    cnx.commit()
    id = cursor.lastrowid
    cursor.close() 
    
    if context == None:
        cnx.close()
    
    return id

def InsertSentenceEntity(user_id, document_id, label_id, start_offset, end_offset, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    id = None
    cursor = cnx.cursor()
    query = ("INSERT INTO api_sequenceannotation (user_id, document_id, label_id, start_offset, end_offset, created_at, updated_at, prob, manual) VALUES ('" + str(user_id) + "', '" + str(document_id) + "', '" + str(label_id) + "', '" + str(start_offset) + "', '" + str(end_offset) + "', now(), now(), 0, 0)")
    cursor.execute(query)
    cnx.commit()
    id = cursor.lastrowid
    cursor.close() 
    
    if context == None:
        cnx.close()

    return id

def SearchPublications(project_id, user_id, context = None):
    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("SELECT pub.create_date, pub.active as status, pub.text as description, pub.file_path, pub.id, pub.pdf_has_annotation  "
            " FROM api_publication pub"
            " inner join api_deparauserteseuperfil depara on depara.teseu_user_id = " + str(user_id) + " and depara.perfil_id = pub.perfil_id"
            " WHERE pub.active = 1 AND pub.processed = 1 AND pub.project_id = '" + str(project_id) + "' order by pub.create_date desc")
    cursor.execute(query)
    
    publications_list = []
    for (create_date, status, description, file_path, id, pdf_has_annotation) in cursor:
        pub = Publications()
        if pdf_has_annotation == 1:
            pub.publication_marcada = "Sim"
        else:
            pub.publication_marcada = "Não"

        pub.publication_date = create_date
        pub.publication_active = status
        pub.publication_text = description
        pub.publication_name = file_path
        pub.publication_id = id
        pub.publication_pdf_has_annotation = pdf_has_annotation
        publications_list.append(pub)

    if len(publications_list) <= 0:
        pub = Publications()
        pub.publication_id = 0
        publications_list.append(pub)
    cursor.close() 
    
    if context == None:
        cnx.close()

    return publications_list

# def GetContador(project_id, context = None):
#     if context != None:
#         cnx = context
#     else:
#         cnx = DbConnect()

#     cursor = cnx.cursor()
#     query = ("SELECT count(*) AS contador FROM api_publication WHERE date(create_date) = date(now()) AND project_id = '" + str(project_id) + "'")
#     cursor.execute(query)
#     count = 0

#     for contador in cursor:
#         c = Contador()
#         c.contador_serial = contador
#         count = c

#     print(count)        

#     cursor.close() 

#     if context == None:
#         cnx.close()

#     return count

def GetUserPerfil(user_id, context = None):

    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = "SELECT perfil_id FROM api_deparauserteseuperfil where teseu_user_id = " + str(user_id) 
    cursor.execute(query)

    _id = ""

    for (perfil_id) in cursor: 
        _id = perfil_id[0]

    cursor.close() 
    
    if context == None:
        cnx.close()

    return _id
    
def GetUserPerfilName(user_id, context = None):

    if context != None:
        cnx = context
    else:
        cnx = DbConnect()

    cursor = cnx.cursor()
    query = ("SELECT name FROM api_perfil " + 
            " INNER JOIN  api_deparauserteseuperfil ON api_deparauserteseuperfil.perfil_id = api_perfil.id " +
            " where teseu_user_id = " + str(user_id))
    
    cursor.execute(query)

    _name = ""

    for (name) in cursor: 
        _name = name[0]

    cursor.close() 
    
    if context == None:
        cnx.close()

    return _name