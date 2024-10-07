import boto3, sys, os
from datetime import date, timedelta
# AMBIENTE #

sys.path.append(os.path.abspath("/usr/spacy/leitor"))
sys.path.append(os.path.abspath("/usr/spacy/leitor/pdf-transform"))
from conn_doccano_ia import CreateLog, GetPublicationList, DeletePublication
from mail_sender import send_clean_s3_error
from DTO import LogType

NOTIFICATION_TO = ""
PROJECT_ID = 1

try:
    data = date.today()
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('')
    publication_list = []
    data_semana_anterior = data- timedelta(weeks=1)
    converted_publication_bd=[]

    try:        
        for obj in bucket.objects.all():
            converted_date = str(obj.last_modified)
            cut_string = converted_date[:10]
            #print(cut_string)
            document = {'KEY': obj.key, 'DATA': cut_string}
            publication_list.append(document)

    except Exception as ex:
        msg = "Erro ao carregar a lista de arquivos do s3: {0}".format(str(ex))
        #print(data, msg)
        raise Exception(msg)

    try:        
        for i in publication_list:
            if ((i['DATA']) <= (str(data_semana_anterior))):
                bucket.Object(i['KEY']).delete()
                #print(i, "Objeto excluido com sucesso !!")

    except Exception as ex:
        msg = "Erro ao excluir os arquivos do s3: {0}".format(str(ex))
        #print(data, msg)
        raise Exception(msg)

    try:
        publication_list_bd = GetPublicationList(PROJECT_ID)
        for pub in publication_list_bd:
            converted_data_bd = str(pub[2])
            cut_string_bd = converted_data_bd[:10]
            document_bd = {'ID': pub[0], 'DATA': cut_string_bd, 'PATH': pub[1]}
            converted_publication_bd.append(document_bd)
    except Exception as ex:
        msg = "Erro ao carregar a lista de publicações para exclusão no banco de dados: {0}".format(str(ex))
        #print(msg)
        raise Exception(msg)
    
    try:
        for i in converted_publication_bd:
            if ((i['DATA']) <= (str(data_semana_anterior))):
                DeletePublication(i['ID'])

    except Exception as ex:
        msg = "Erro ao excluir publicações do banco de dados: {0}".format(str(ex))
        #print(msg)
        raise Exception(msg)

except Exception as ex:
    send_clean_s3_error(str(ex), NOTIFICATION_TO)
    CreateLog("clean_s3: Erro ao executar", LogType.error.name, message=str(ex))
    #print(data, "Erro de execução")
