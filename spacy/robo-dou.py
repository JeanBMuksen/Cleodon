# _*_ coding: utf-8 _*_
import spacy
import fitz
import sys, json
import fpdf
import re
import tika
from tika import parser
from datetime import datetime
from spacy.lang.pt import Portuguese
from spacy.lang.pt.stop_words import STOP_WORDS
import pt_core_news_sm
from spacy import displacy
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer
from sklearn.base import TransformerMixin
from sklearn.pipeline import Pipeline
import string
from spacy.util import minibatch, compounding
import random
import os
import nltk
import nltk.corpus
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktTrainer, PunktParameters
from nltk.tokenize import word_tokenize
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
import boto3
import botocore
import threading
from urllib import parse

#################################################################

PATH_AMBIENTE_DATA = "" 

IMPORT_PATHS = [""]

sys.path.append(os.path.abspath(IMPORT_PATHS[0]))
sys.path.append(os.path.abspath(IMPORT_PATHS[1]))

#################################################################

from conn_doccano_ia import DbConnect, CreateLog, GetSentenceAnnotation, InsertSentence, InsertSentenceEntity, GetEntityId, InsertEntity, GetPublicationQueueByProject, UpdateProcessedPublication, RollBackPublicationProcess, ActivatePublication , GetEntityIdList, GetBlackList #, RollbackSentence
from DTO import LogType
from PyPDF2 import PdfFileWriter, PdfFileReader
import math

#max thread simultaneously    
semaphore = threading.BoundedSemaphore(2)

#número iterações utilizadas pela I.A no seu treinamento
N_ITER = 80

# default project
PROJECT_ID = 1
# default user_id
USER_ID = 1

#aws bucket to store files
BUCKET_S3 = ''

parser = Portuguese()
tika_parser = parser

color = {"stroke": (1, 0.52, 0)}
color2 = {"stroke": (0, 1, 0)}

def round_up(n, decimals=0): 
    multiplier = 10 ** decimals 
    return math.ceil(n * multiplier) / multiplier

#as identified, sometimes tika fails to start server on "from_file" method invoke even with the 3 default attempts to connect. This is a workaround to try 3 more attempts.
def From_file_tika_parser(publication_id, page, tika_parser, file_path, attempt_count = 1):
    loop_break = False
    try:
        #msgp = "from_file_tika_parser - publication_id {0}  - page {1} - attempt {2}".format(str(publication_id), str(page), str(attempt_count))
        #print(msgp)
        return tika_parser.from_file(file_path)
    except Exception as e:
        #msgp = "from_file_tika_parser - publication_id {0} - page {1} - attempt {2} - error: {3}".format(str(publication_id), str(page), str(attempt_count), str(e).replace("\'", "")) 
        #print(msgp)
        if attempt_count <= 3:
            attempt_count = attempt_count +1
            #retry = "from_file_tika_parser - publication_id {0}  - page {1} - retrying attempt {2}".format(str(publication_id), str(page), str(attempt_count))
            #print(retry)
            return From_file_tika_parser(publication_id, page, tika_parser, file_path, attempt_count = attempt_count)
        else:
            try:
                #msgp = "from_file_tika_parser - publication_id {0} - page {1} - attempt {2} - importing again, attempt -1 to try again".format(str(publication_id), str(page), str(attempt_count))
                #print(msgp)

                if loop_break == True:
                    raise e

                loop_break = True

                from tika import parser
                tika_parser = parser
                attempt_count = attempt_count -1
                return From_file_tika_parser(publication_id, page, tika_parser, file_path, attempt_count = attempt_count)
            except Exception as ee:
                raise ee

def DataTrainning(project_id, perfil_id):
    #print("get trainning data - begin")
    sentenceAnnot_list = GetSentenceAnnotation(True, project_id, perfil_id)
    train_data = []
    unique_sentence_list = []
    isUnic = True #check unique sentence

    #carrega a lista de sentenças de treinamento retiradas da base de treinamento
    for sentence in sentenceAnnot_list:
        for x in unique_sentence_list:
            if sentence.document_text == x.document_text:
                isUnic = False
                break
        if isUnic:
            unique_sentence_list.append(sentence)
        isUnic = True

    ner_labels = []
    isUnic = True #check unique ner_labels
    for sentence in unique_sentence_list:
        sentence_labels = []
        #print("sentence: ", sentence.document_id, sentence.document_text, sentence.label_text)
        for x in sentenceAnnot_list:
            if x.document_id == sentence.document_id:
                #print("label: ", x.document_id, x.document_text, x.label_text)
                if x.start_offset != None and x.end_offset != None and x.label_text != None:
                    sentence_labels.append((x.start_offset, x.end_offset, x.label_text))

                #adicona a label no new label sem repetir
                for lbl in ner_labels:
                    if x.label_text == lbl:
                        isUnic = False
                        break
                if isUnic:
                    if x.label_text != None:
                        ner_labels.append(x.label_text)
                isUnic = True

        train_data.append((sentence.document_text, {"entities": sentence_labels}))

    #print("get trainning data - end")
    for pub in train_data:
        print(pub)
        print("\n")
        
    return (train_data, ner_labels, perfil_id)
    

def Treinner(ner_labels, train_data):
    # seta modulo nlp para a linguagem portuguesa
    nlp = Portuguese()    

    # carrega os tokens dentro do modulo sentencizer para criar as sentenças
    sdb = nlp.create_pipe('sentencizer')
    nlp.add_pipe(sdb)

    # carrega a lista de stop words para delimitar as sentenças
    spacy_stopwords = spacy.lang.pt.stop_words.STOP_WORDS
    #print('Number of stop words: %d' % len(spacy_stopwords))
    #print('First ten stop words: %s' % list(spacy_stopwords)[:20])

    # carrega a lematização no sentenciador, lingua portuguesa
    lem = nlp("correr correndo corre corredor")
    # for word in lem:
    #     print (word.text, word.lemma_)
            
    #carrega o conteudo da lematização no sentenciador e define os objetos linguisticos
    nlp = pt_core_news_sm.load()

    docs = nlp(u"Tudo está bem quando termina bem.")
    # for word in docs:
    #     print(word.text, word.pos_)

    mango = nlp(u'coffito')
    # print(mango.vector.shape)
    # print(mango.vector)

    punctuations = string.punctuation

    #indica ao processador de linguagem natural que o idioma será em portuges
    # nlp = spacy.load('pt')
    #início do treinamento do módulo nlp

    nlp = spacy.blank('pt')

    reset_weights = False
    if "ner" not in nlp.pipe_names:
            ner = nlp.create_pipe("ner")
            nlp.add_pipe(ner, last=True)
            reset_weights = True
            #print("criou ner")
    else:
        ner = nlp.get_pipe("ner")

    for label in ner_labels:
        ner.add_label(label)  
        #assert label in ner.labels

    optimizer = nlp.begin_training()

    move_names = list(ner.move_names)

    #print("move names:", move_names)

    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    #print("iniciando processamento nlp")
    #print("------------------- ORGANIZED TRAIN DATA")
    #print(train_data)
    with nlp.disable_pipes(*other_pipes):  
        sizes = compounding(1.0, 4.0, 999)
        #sizes = compounding(0.9, 3.5, 999)

        for itn in range(N_ITER):
            random.shuffle(train_data)
            batches = minibatch(train_data, size=sizes)
            losses = {} 
            for batch in batches:
                texts, annotations = zip(*batch)
                #print("Publicação: {0}, page: {1}, Iteração: {2} \n".format(publication_id, str(page), itn))
                #print("texts:", texts)
                #print("ann:", annotations)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.34, losses=losses) #nlp.update(texts, annotations, sgd=optimizer, drop=0.21, losses=losses)
                #print("Losses", losses)

    #final = (displacy.render(doc, style = "ent"))
    return nlp


def ProcessPublication(project_id, user_id, publication_id, local_file_path, file_path_aws, publication_text, tika_parser, train_data, ner_labels, s3, perfil_id):
    CreateLog("robo_dou-ProcessPublication: Processo iniciado para a publicação id: ({0})!".format(publication_id), LogType.info.name, reference_name="publication_id", reference_id=publication_id)
    print("comecou")
    
    #print("processando publicação: ", publication_id)
    #variable initialized to be used in try and catch.
    local_file_path_marcado = ""
    local_file_path_marked_filtered = ""
    output_page_file = ""
    pdf_annot = None
    page_has_annotation = False
    any_annotation = False
    onlyMarkedPages = []
    pdf_annot_filtered = None
    pdf = None
    context = None
    cursor = None
    try:
        nlp = Treinner(ner_labels, train_data)
        print("treinou")
        # abre o pdf a ser marcado via fitz
        pdf_annot = fitz.open(local_file_path)
        # pdf_annot_filtered = fitz.open()
        pdf_annot_filtered = PdfFileWriter()

        # percorre as páginas do pdf 
        with open(local_file_path, "rb") as lf:
            pdf = PdfFileReader(lf)
            print("abriu pdf para leitura e separacao de paginas")
            for page in range(pdf.getNumPages()):
                page_has_annotation = False
                #print("processando página: ", page)

                # print("########################################################################")
                #todo: remover limitação produção
                # if page > 5:
                #     break
                # cria um pdf com a página atual
                pdf_writer = PdfFileWriter()
                current_page = pdf.getPage(page)
                pdf_writer.addPage(current_page)

                #create unic temp file name to be used for each thread
                temp_pdf_name = str(datetime.today()).replace(" ", "-").replace(":", "-").replace(".", "-") + "_temp_" + str(publication_id) + "_" + str(perfil_id) + ".pdf"

                output_page_file = PATH_AMBIENTE_DATA + temp_pdf_name

                with open(output_page_file, "wb") as out:
                    pdf_writer.write(out)
                #print("criou pdf página")

                #carrega texto do arquivo temporário que contém a página 
                data = From_file_tika_parser(publication_id, page, tika_parser, output_page_file)

                # extrai texto do pdf
                text = data['content']

                #busca o black list
                Black_list = GetBlackList()

                #convert para str
                text = str(text)

                #limpa as black_words
                for word in Black_list:
                    text = text.replace(word[0], '')

                #remove temp file
                os.remove(output_page_file)

                #corrige espaços em brancos resultantes da importação do pdf
                patt = re.compile('(\\s*)\\n\\n\\n(\\s*)')

                never_space = patt.sub('', text)

                doc = nlp(never_space)
                # i.text = label encontrada, i.label_ = label pesquisada
                #entities=[(i.text, i.label_, i.start_char, i.end_char) for i in doc.ents]
                #print("entities:", entities)

                # OUTPUT
                # file.write(str.encode(final))
                # file.close()

                # entidades encontradas no treinamento
                entities=[(i.text) for i in doc.ents] #, i.start_char, i.end_char
                # for lbl in entities:
                #     print("Label: ", lbl)

                # extrai as entidades repetidas
                unique_entities = []
                isUnic = True #check unique entities
                for lbl in entities:
                    for unique in unique_entities:
                        if lbl == unique:
                            isUnic = False
                            break
                    if isUnic:
                        unique_entities.append(lbl)
                    isUnic = True

                for lbl in unique_entities:
                    print("Label unique: ", lbl)

                trainer = PunktTrainer()
                trainer.INCLUDE_ALL_COLLOCS = True
                doc_text = (doc.text).replace('.\n\n§', ';\n\n§')
                #sent_text = nltk.sent_tokenize(doc_text)
                trainer.train(doc_text)
                
                tokenizer = PunktSentenceTokenizer(trainer.get_params())
                #tokenizer._params.abbrev_types.add('art')
                #tokenizer._params.abbrev_types.add('§')

                punkt_param = PunktParameters()
                abbreviation = ['\\n\\n', '§','EMBRAPA\\n\\nFLORESTA RESULTADO DE JULGAMENTO\\nPREGÃO Nº 1/2020\\n\\nA Embrapa Florestas torna público o resultado final do Pregão Eletrônico 001/2020, cujo objetoé o registro para eventual aquisição de serviços de manutenção com fornecimento de peças para veículos leves e caminhonetes da frota da Embrapa Florestas. Empresa Vencedora: FITALFA AUTO MECÂNICA LTDA CNPJ 03.971.648/0001-01 Valor Total R$ 201.863,90\\n\\nREJANE SRTUMPF SBERZE Chefe Adjunto de Administração\\n\\n(SIDEC - 13/05/2020) 135028-13203-2020NE800027', 'Art. 39. A parte poderá desistir da inquirição de qualquer uma das testemunhas arroladas, ressalvado o direito da Comissão de Ética de ouvi-las, se assim entender pertinente.']
                punkt_param.abbrev_types = set(abbreviation)
                tokenizer = PunktSentenceTokenizer(punkt_param)
                tokenizer.train(doc_text)

                #AI = AI.replace('inciso', '§')
                
                #print tokenizer.tokenize(sentences)
                
                #for decision in tokenizer.debug_decisions(sentences):
                #    pprint(decision)
                #    print '=' * 30

                # now loop over each sentence and tokenize it separately
                sent_text = tokenizer.tokenize(doc_text) # this gives us a list of sentences
                #sent_text = nltk.sent_tokenize(AI) # this gives us a list of sentences
                #print("Tratando sentencas e labels - publicação: {0}".format(publication_id))
                sentence_labels = []
                offset, length, offsetlabel = 0, 0, 0

                entity_data = GetEntityIdList(project_id)

                context = DbConnect()
                cursor = context.cursor()
                commitAtZero = 1000
                for sentence in sent_text:
                    tokenized_text = nltk.word_tokenize(sentence)
                    tagged = nltk.pos_tag(tokenized_text)
                    #print('\n-----\n')
                    #sentence = sentence.replace(';\n\n\n§', '.\n\n\n§')
                    while doc_text[offset] != sentence[0]:
                        offset += 1
                    
                    length = len(sentence)
                    #print("\n###sentença:\n", sentence, "\n\n###offset: ", offset, "\n###length", length)
                    offset += length

                    # salvar a sentença
                    sentence_id = InsertSentence(sentence, project_id, page, publication_id)
                    has_annotation = False
                    # print (sentence)
                    # print ("\n##############################################################\n")

                    label_in_sentence_list = []

                    for lbl in unique_entities:
                        #label_id = GetEntityId(lbl, project_id)#, context = context)
                        label_id = None
                        for entity in entity_data:
                            if entity[1].lower() == lbl.lower():
                                label_id = entity[0]
                                break

                        if label_id == None:
                            continue

                        #print("start searching label: ", lbl)
                        keepSearching = True
                        last_offset = -1
                        while(keepSearching):
                            start_index = 0
                            if last_offset >= 0:
                                #print("last_offset", last_offset)
                                start_index = last_offset + len(lbl)
                                #print("start_index: ", start_index)
                            
                            offset_label = -1
                            if lbl != None and lbl.strip() != '' and len(lbl) >= 3:
                                offset_label = sentence.find(lbl, start_index, len(sentence))
                                #print("found offset: ", offset_label)

                            if offset_label != -1:
                                # guarda o offset_label para posterior controle
                                last_offset = offset_label

                                #todo: check if this flow is necessary. está gravando a sentença (linha 363), mesmo que a anotação não seja gravada devido a não ter label (código abaixo comentado)
                                #if label_id == None or label_id <= 0: # caso a entidade ainda não exista, adiciona e utilizada como referência posterior
                                    #label_id = InsertEntity(lbl, project_id, context = context)
                                
                                if label_id != None and label_id > 0:
                                    # guarda na lista a ser utilizada
                                    label_in_sentence_list.append(lbl)
                                    has_annotation = True   

                                    #print("user_id: ", user_id, ", sentence_id: ", sentence_id, ", label_id: ", label_id, ", offset_label: ", offset_label, ", end_offset: ", offset_label + len(lbl))
                                    # salvar a label da entidade encontrada na sentença
                                    InsertSentenceEntity(user_id, sentence_id, label_id, offset_label, offset_label + len(lbl), context = context, cursor = cursor, parentCommit = True) #, context = context)
                                    commitAtZero = commitAtZero -1
                                    if commitAtZero == 0:
                                        context.commit()
                                        commitAtZero = 1000
                                
                                #context.close()
                                #print ("lbl: ", lbl, "offset: ", offset_label)
                            else:
                                keepSearching = False
                                #print ("lbl: ", lbl, "offset: não encontrado.")

                    #print (label_in_sentence_list)
                    #print ("\n##############################################################\n")

                    if has_annotation:
                        # sentence + labels, para marcar no PDF com o high light
                        sentence_labels.append((sentence, label_in_sentence_list))
                    # else:
                    #     RollbackSentence(sentence_id) #rollback removed because sentence need to be saved even if there's no label for it


                if commitAtZero > 0 and commitAtZero < 1000:
                    context.commit()
                    
                cursor.close()
                context.close()
                context = None

                # print sentence and its labels
                # for sent in sentence_labels:
                #     print("\n### SENTENCE ################################################################################\n")
                #     print(sent[0])
                #     print("\n--- LABEL --------------------------------------------------------------------------------\n")
                #     for lbl_print in sent[1]:
                #         print("label: ", lbl_print[0], "\n")

                unique_label_list = []
                isUnic = True
                pdf_annot_page = pdf_annot[page] # "page" é o index da página do pdf aberto para leitura e processamento da ia via PdfFileReader, que consequentemente é o mesmo index da página do pdf aberto para marcação via fitz

                # percorre as sentenças que contém o texto da sentença na posição [0] e a lista das suas labels na posição [1]
                for sent in sentence_labels:
                    # recupera o texto da senteça
                    sentence_adicionada = sent[0]

                    # marca apenas as sentenças que tem label para marcar
                    if any(sent[1]):
                        if page_has_annotation == False:
                            page_has_annotation = True
                            any_annotation = True


                    #     #print("############# Sentença: \n", sentence_adicionada,"\n")
                        
                    ##########################################################################################################
                    #     # marca a sentença por partes, pois pesquisando ela inteira não está grifando corretamente no pdf
                    ##########################################################################################################
                    #     sentence_len = len(sentence_adicionada)
                    #     #print(sentence_len)
                    #     string_group_amount = 50
                    #     sentence_word_wrap = sentence_adicionada.split(' ')
                    #     string_group_count = 0
                    #     if sentence_word_wrap != None and sentence_word_wrap != [] and len(sentence_word_wrap) > 50:
                    #         string_group_count = int(round_up(sentence_len / string_group_amount))
                    #         #print("string_group_count :", string_group_count)
                    #     sentenca_quebrada = []
                    #     if string_group_count > 0:
                    #         start_index_slice = 0
                    #         for div in range(string_group_count):
                    #             #print("start_index: ", start_index_slice, ", quant: ", string_group_amount)
                    #             #print("div: ", div)
                    #             #print("word_group: ", sentence_adicionada[start_index_slice:string_group_amount])
                    #             string_group = ""
                    #             for i in range(string_group_amount):
                    #                 if (start_index_slice -1) + i < sentence_len -1:
                    #                     #print("index: ", start_index_slice + i)
                    #                     string_group += sentence_adicionada[start_index_slice + i]
                    #             #print("word_group: ", string_group)
                    #             #print("sentence:", sentence_adicionada)
                    #             sentenca_quebrada.append(string_group)
                    #             start_index_slice = ((div + 1) * string_group_amount)
                    #             #print("start_index: ", start_index_slice, ", quant: ", string_group_amount)

                    #     if sentenca_quebrada == []:
                    #         # pesquisa sentenca no pdf.
                    #         pesquisa = pdf_annot_page.searchFor(sentence_adicionada)
                    #         # percorre o resultado da pesquisa, adicionando highlight 
                    #         for inst in pesquisa:
                    #             #print("############ Pesquisa: \n", inst, "\n")
                    #             marcador = pdf_annot_page.addHighlightAnnot(inst)
                    #             marcador.update()
                    #     else:
                    #         for senti in sentenca_quebrada:
                    #             # pesquisa sentenca no pdf.
                    #             pesquisa = pdf_annot_page.searchFor(senti)
                    #             # percorre o resultado da pesquisa, adicionando highlight 
                    #             for inst in pesquisa:
                    #                 #print("############ Pesquisa: \n", inst, "\n")
                    #                 marcador = pdf_annot_page.addHighlightAnnot(inst)
                    #                 marcador.update()
                    #####################################################
                    # end of sentence markup
                    #####################################################
                    
                        # percorre a lista de labels da sentença
                        for lbl_check in sent[1]:
                            #print("######## label: ", lbl_check, "\n")

                            # cria lista única de labels a serem marcadas no pdf
                            for unique_label in unique_label_list:
                                if unique_label == lbl_check:
                                    isUnic = False
                                    break

                            if isUnic:
                                unique_label_list.append(lbl_check)

                            isUnic = True

                # percorre a lista de labels únicas para marcar no pdf
                for unique_label in unique_label_list:
                    print("######## label única: ", unique_label, "\n")
                    # pesquisa a label no pdf
                    pesquisa_lbl = pdf_annot_page.searchFor(unique_label, hit_max=999)
                    # percorre o resultado da pesquisa, adicionando highlight
                    for inst_lbl in pesquisa_lbl:
                        marcador_label = pdf_annot_page.addHighlightAnnot(inst_lbl)
                        #marcador_label.setColors(color2)
                        marcador_label.update()
                
                if page_has_annotation == True:
                    onlyMarkedPages.append(page)
                #     pdf_annot_filtered.insertPDF(
                #         pdf_annot,          # cannot be the same object as doc1
                #         from_page=page,   # first page to copy, default: 0
                #         to_page=page,     # last page to copy, default: last page
                #         links=True,    # also copy links
                #         annots=True,   # also copy annotations
                #     )
            
            ### fim do iteração das páginas do pdf do diário oficial da união
            print("processou todas as paginas")
            #save annoted pdf local before upload to aws s3 "marcado"
            local_file_path_marcado = local_file_path.replace(".pdf", "_marcado_" + str(perfil_id) + ".pdf")
            pdf_annot.save(local_file_path_marcado)
            pdf_annot.close()
                    
            #create aws file path to annoted pdf "marcado"
            file_path_aws_marcado = file_path_aws.replace(".pdf", "_marcado_" + str(perfil_id) + ".pdf")

            #todo: make the file upload to be executed more two times if it gets error.
            s3.Bucket(BUCKET_S3).upload_file(local_file_path_marcado, file_path_aws_marcado) #from local file path upload option
            #s3.Bucket(BUCKET_S3).put_object(Key=file_path_aws_marcado, Body=open(local_file_path_marcado, 'rb')) #from file bytes upload option (not shure if works because firt option is the best way and worked fine)
            
            #save filtered annoted pdf local before upload to aws s3 "marcado_filtrado"
            if any_annotation == True:
                print("has annotation")
                local_file_path_marked_filtered = local_file_path_marcado.replace(".pdf", "_filtrado.pdf")

                with open(local_file_path_marcado, "rb") as f:
                    pdf_annoted = PdfFileReader(f)

                    for markedPage in onlyMarkedPages:
                        pdf_annot_filtered.addPage(pdf_annoted.getPage(markedPage))
                    
                    with open(local_file_path_marked_filtered, "wb") as out:
                        pdf_annot_filtered.write(out)
                
                # pdf_annot_filtered.save(local_file_path_marked_filtered)
                # pdf_annot_filtered.close()
                print("created only marked pdf")
                #create aws file path to filtered annoted pdf "marcado_filtrado"
                file_path_aws_marcado_filtered = file_path_aws_marcado.replace(".pdf", "_filtrado.pdf")

                #todo: make the file upload to be executed more two times if it gets error.
                s3.Bucket(BUCKET_S3).upload_file(local_file_path_marked_filtered, file_path_aws_marcado_filtered) #from local file path upload option

        #remove local_file_path_marcado  after uploaded to aws s3
        if os.path.isfile(local_file_path_marcado) == True:
            os.remove(local_file_path_marcado)
        
        #remove local_file_path_marked_filtered after uploaded to aws s3
        if os.path.isfile(local_file_path_marked_filtered) == True:
            os.remove(local_file_path_marked_filtered)
        
        #remove local_file_path after I.A process
        # if os.path.isfile(local_file_path) == True:
        #     os.remove(local_file_path)
        
        # set publication as processed, if any_annotation so pdf_has_annotation.
        UpdateProcessedPublication(publication_id, any_annotation)
        #print("processamento finalizado")
        
        CreateLog("robo_dou-ProcessPublication: Publicação processada com sucesso!", LogType.success.name, reference_name="publication_id", reference_id=publication_id)

        pdf_annot_filtered = None
    except Exception as exce:
        print("ProcessPublication - publication_id: {0} - error: {1} ".format(publication_id, str(exce)))
        print("exception ProcessPublication: ", str(exce))

        #parentCommit context
        if cursor != None:
            cursor.close()
        if context != None:
            context.close()

        if any_annotation == True:
            pdf_annot_filtered = None
            # if pdf_annot_filtered != None:
            #     try:
            #         pdf_annot_filtered.close()
            #     except Exception as excepp:
            #         pass
            
            if os.path.isfile(local_file_path_marked_filtered) == True:
                #pdf_annot_filtered
                os.remove(local_file_path_marked_filtered)

        if pdf_annot != None:
            try:
                pdf_annot.close()
            except Exception as excep:
                pass

        if os.path.isfile(local_file_path_marcado) == True:
            #pdf_annot
            os.remove(local_file_path_marcado)
        
        # if os.path.isfile(local_file_path) == True:
        #     #source pdf from processment and annotations
        #     os.remove(local_file_path)
        
        if os.path.isfile(output_page_file) == True:
            #temp pdf fro processment
            os.remove(output_page_file)

        cnx = DbConnect()
        
        CreateLog("robo_dou-ProcessPublication: Erro ao processar a publicação", LogType.error.name, message=str(exce), reference_name="publication_id", reference_id=publication_id, context=cnx)
        
        print("calling RollBackPublicationProcess")
        RollBackPublicationProcess(publication_id, str(exce), context=cnx)
        print("Rollback Done")
        cnx.close()

def thread_process_publication(project_id, user_id, publication_id, file_path_aws, publication_text, tika_parser, train_data, ner_labels, s3, perfil_id):    
    try:
        ActivatePublication(publication_id, False)
        path = ""
        semaphore.acquire()
        try:

            #print("iniciando processamento da publicação:", publication_id)
            
            #create local path to save pdf from aws to be used by I.A process
            #download file by aws s3            
            path = PATH_AMBIENTE_DATA + file_path_aws            
            s3.Bucket(BUCKET_S3).download_file(file_path_aws, path)
        except Exception as exc:
            path = ""
            #print("robo_dou-thread_process_publication: Erro ao recuperar arquivo do s3 para processar a publicação")
            CreateLog("robo_dou-thread_process_publication: Erro ao recuperar arquivo do s3 para processar a publicação", LogType.error.name, message=str(exc), reference_name="publication_id", reference_id=publication_id)
            ActivatePublication(publication_id, True)
            print("erro 12: ", str(exc))
            
        if path != "":
            ProcessPublication(project_id, user_id, publication_id, path, file_path_aws, publication_text, tika_parser, train_data, ner_labels, s3, perfil_id)

        semaphore.release()
    except Exception as ex:
        CreateLog("robo_dou-thread_process_publication: Erro ao reservar publicação para iniciar o processamento!", LogType.error.name, message=str(ex), reference_name="publication_id", reference_id=publication_id)
        ActivatePublication(publication_id, True)
        print("erro 1: ", str(ex))

def robo_dou(project_id, user_id):
    try:
        # get publication queue
        publication_list = GetPublicationQueueByProject(project_id)      

        if publication_list != None and publication_list != []:
            s3 = boto3.resource('s3')

            trainning_info = []
            loaded_data_trainning_perfil_list = []
            for pub in publication_list:             
                loaded_data_trainning = None
                if pub[3] not in loaded_data_trainning_perfil_list:
                    loaded_data_trainning_perfil_list.append(pub[3])
                    loaded_data_trainning = DataTrainning(project_id, pub[3])
                    trainning_info.append(loaded_data_trainning)
                
                # if not loaded in this iteration, get loaded data already loaded before
                if loaded_data_trainning == None:
                    for dt in trainning_info:
                        if dt[2] == pub[3]:
                            loaded_data_trainning = dt
                            break

                if loaded_data_trainning != None:
                    #threads will be finished automatically after end of the called methods
                    _thread = threading.Thread(target=thread_process_publication, args=(project_id, user_id, pub[0], pub[1], pub[2], tika_parser, loaded_data_trainning[0], loaded_data_trainning[1], s3, pub[3]))
                    _thread.start()
    except Exception as ex:
        #print("robo_dou-main: Erro ao executar processamento de I.A.")
        CreateLog("robo_dou-main: Erro ao executar processamento de I.A.", LogType.error.name, message=str(ex))
        print("erro 13: ", str(ex))
        
robo_dou(PROJECT_ID, USER_ID)