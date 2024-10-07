# _*_ coding: utf-8 _*_
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
#from django.core.context_processors import csrf
from django.contrib import messages, sessions
from django.views.generic import ListView
from datetime import date
from .models import Usuario, Arquivo
from .DTO import Publications, SentenceAnnotation
from .conn_doccano import SearchPublications, GetUserPerfil, GetUserPerfilName
import boto3
import botocore
import os, sys
from .CopyPDF import CopyPdfPages
import webbrowser
import requests
import urllib.parse

PROJECT_ID = 1
BUCKET_NAME = ""

AMBIENTE = ["/usr/spacy/leitor/static/data/{0}", "/"]


def index(request):
    return render(request,'index.html', {})

@csrf_protect
def login_user(request):
    return render(request,'login.html')

def teste(request):
    return render(request,'teste.html')


# todo: load all necessary data to load and reload the HomeLogado.html template.     
@csrf_protect
def home(request):
    user_id = request.session.get('_auth_user_id', '')
    if user_id != '':        
        # contador = GetContador(1)
        #print("home user_id", user_id)
        return render(request, 'HomeLogado.html', {'user_id': user_id})
    else : 
        return redirect('/login')

@csrf_protect
def submit_login(request):
    if request.POST:
        username = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(username=username, password=password)

                
        
        if user is not None:
            login(request, user)
            user_id = request.session.get('_auth_user_id', '')
            perfil_name = GetUserPerfilName(user_id)
            #print("login user_id", user_id)
            return render(request, 'HomeLogado.html', {'user_id': user_id, 'perfil_name': perfil_name})
        else:
            messages.error(request, 'Usuário e senha invalidos')

    return redirect('/login')    

@csrf_protect
def logout_user(request):
    logout(request)
    return redirect('/login')


# def carregarpdf(request, file_name, file_path_filtered, pub_id):
#     if file_name != None and file_name != '':
#         count = 1
#         verifica_list = "1,2,3"
#         return render(request,'HomeLogado.html', {"file_name": file_name, "count": count, "file_path_filtered": file_path_filtered, "verifica_list": verifica_list, "pub": pub})
#     else:
#         return render(request,'HomeLogado.html')
        
@csrf_protect
def carrega_lista(request):
    user_id = request.session.get('_auth_user_id', '')
    publication_list = SearchPublications(PROJECT_ID, user_id)
    perfil_name = GetUserPerfilName(user_id)
    #print("carrega_lista user_id", user_id)
    state = 0
    return render(request, "HomeLogado.html", {'publication_list': publication_list, "file_name": "", "exported_file_path": "", "user_id": user_id, "perfil_name": perfil_name, "state": state})

@csrf_protect
def carrega_lista_download(request):
    user_id = request.session.get('_auth_user_id', '')
    publication_list = SearchPublications(PROJECT_ID, user_id)
    perfil_name = GetUserPerfilName(user_id)
    state = 1
    #print("carrega_lista user_id", user_id)
    return render(request, "HomeLogado.html", {'publication_list': publication_list, "file_name": "", "exported_file_path": "", "user_id": user_id, "perfil_name": perfil_name, "state": state})
    
                                                                       
@csrf_protect
def LoadPdfAnnotation(request):
    user_id = request.session.get('_auth_user_id', '')
    perfil_id = GetUserPerfil(user_id)
    perfil_name = GetUserPerfilName(user_id)
    #print("LoadPdfAnnotation user_id", user_id)
    count = 1

    file_path_filtered = ""
    file_path = None
    if request.POST:

        pub_id = request.POST.get('data2')
        file_path_aws = request.POST.get('data1').replace(".pdf", "_marcado_" + str(perfil_id) + ".pdf")


        pdf_has_annotation = request.POST.get('hdn_pdf_has_annotation')

        local_file_base_path = AMBIENTE[0]

        local_file_path = local_file_base_path.format(file_path_aws)
        
        local_file_path_filtered = local_file_path.replace(".pdf", "_filtrado.pdf")
        
        file_path = "/data/" + file_path_aws

        s3 = boto3.resource('s3')

        try:
            #check if file already exists before download it

            #all pages
            if os.path.isfile(local_file_path) == False:
                s3.Bucket(BUCKET_NAME).download_file(file_path_aws, local_file_path)
            
            if int(pdf_has_annotation) == 1:
                file_path_filtered = file_path.replace(".pdf", "_filtrado.pdf")
                #only marked pages..
                if os.path.isfile(local_file_path_filtered) == False:
                    file_path_aws_filtered = file_path_aws.replace(".pdf", "_filtrado.pdf")
                    s3.Bucket(BUCKET_NAME).download_file(file_path_aws_filtered, local_file_path_filtered)

        except botocore.exceptions.ClientError as e:
            # if e.response['Error']['Code'] == "404":
            #     print("O Objeto não existe no s3, download não realizado.")
            # else:
            #     print("oto erro no download do s3.")
            #     raise
            raise e

        if file_path != None and file_path != '':
            return render(request,'HomeLogado.html', {"file_name": file_path, "count": count, "file_path_filtered": file_path_filtered, "pub_id": pub_id, "user_id": user_id, "perfil_name": perfil_name})
    
    return render(request,'HomeLogado.html', {"user_id": user_id, "perfil_name": perfil_name})
    
    #return carregarpdf(request, file_path, file_path_filtered, pub_id)
def editLabel(request):
    user_id = request.session.get('_auth_user_id', '')
    perfil_name = GetUserPerfilName(user_id)
    
    return render(request, 'HomeLogado.html', {"user_id": user_id, "perfil_name": perfil_name})

@csrf_protect
def exportPDF(request):
    user_id = request.session.get('_auth_user_id', '')
    perfil_id = GetUserPerfil(user_id)
    perfil_name = GetUserPerfilName(user_id)
    #print("exportpdf user_id", user_id)
    count = 0

    if request.GET:

        ########## export begin
        exported_file_error = "" # Apresenta este erro via javascript caso exista ao renderizar!
        exported_file_path = ""
        pub_id = ""

        export_file_path = request.GET.get('file_path')
        if export_file_path != None and export_file_path != "":
            try: 
                pub_id = request.GET.get('id')
                export_pages = request.GET.get('pages')
                remove_mark = request.GET.get('remove_mark')
                if remove_mark == 'true':
                    export_file_path = export_file_path.replace("_marcado_" + str(perfil_id) + ".pdf", ".pdf")

                file_path_aws = export_file_path.replace("/data/", "")

                s3 = boto3.resource('s3')
                try:
                    #check if file already exists before download it
                    export_file_path = AMBIENTE[0].format(export_file_path.replace("/data/", "")).replace("/", AMBIENTE[1])

                    if os.path.isfile(export_file_path) == False:
                        s3.Bucket(BUCKET_NAME).download_file(file_path_aws, export_file_path)
                
                except botocore.exceptions.ClientError as e:
                    # if e.response['Error']['Code'] == "404":
                    #     print("O Objeto não existe no s3, download não realizado.")
                    # else:
                    #     print("oto erro no download do s3.")
                    #     raise
                    raise e

                exported_file_path = CopyPdfPages(export_file_path, file_path_aws, export_pages, user_id)
            except Exception as ee:
                exported_file_error = str(ee)
            
            return render(request,'HomeLogado.html', {"file_name": "", "exported_file_path": exported_file_path, "exported_file_error": exported_file_error, "count": count, "pub_id": pub_id, "user_id": user_id, "perfil_name": perfil_name})
        ########## export end
    
    return render(request,'HomeLogado.html', {"user_id": user_id, "count": count, "perfil_name": perfil_name})

@csrf_protect
def downloadPDF(request):
    user_id = request.session.get('_auth_user_id', '')
    perfil_id = GetUserPerfil(user_id)
    perfil_name = GetUserPerfilName(user_id)
    #print("LoadPdfAnnotation user_id", user_id)
    count = 1

    file_path_filtered = ""
    file_path = None
    if request.POST:

        pub_id = request.POST.get('data2')
        file_path_aws = request.POST.get('data1')
        print("--------------")
        print(file_path_aws)

        local_file_base_path = AMBIENTE[0]

        local_file_path = local_file_base_path.format(file_path_aws)

        s3 = boto3.resource('s3')

        try:
            #check if file already exists before download it

            #all pages
            s3.Bucket(BUCKET_NAME).download_file(file_path_aws, local_file_path)

        except botocore.exceptions.ClientError as e:
            # if e.response['Error']['Code'] == "404":
            #     print("O Objeto não existe no s3, download não realizado.")
            # else:
            #     print("oto erro no download do s3.")
            #     raise
            raise e

        # if file_path != None and file_path != '':
        #     return render(request,'HomeLogado.html', {"file_name": file_path, "count": count, "file_path_filtered": file_path_filtered, "pub_id": pub_id, "user_id": user_id, "perfil_name": perfil_name})
    
    return render(request,'HomeLogado.html', {"user_id": user_id, "perfil_name": perfil_name})

@csrf_protect
def redirectDoccano(request):
    # r = requests.post(url, data=values)
    return render(request,'HomeLogado.html')