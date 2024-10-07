# _*_ coding: utf-8 _*_
import fitz
import os
from PyPDF2 import PdfFileReader
from datetime import date
#import secrets

def CopyPdfPages(file_path, file_name, pages, user_id):
    #print("copying pdf")

    pages = pages.split(',') #javascript validation accepts only string like: 1,2,3-10,78

    #unic = secrets.token_urlsafe(16) #change to user_id to create only one pdf export by user
    sulfix = "_exportado_" + str(user_id) +  ".pdf"
    new_file_path = "/data/temp/" + file_name.replace(".pdf", sulfix)

    #################################
    # AMBIENTE #

    # windows path - localhost
    #new_pdf_path = file_path.replace("\\data\\", "\\data\\temp\\").replace(".pdf", sulfix)

    # linux path - homolog
    new_pdf_path = file_path.replace("/data/", "/data/temp/").replace(".pdf", sulfix)
    ################################

    opened_pdf_to_be_copied = fitz.open(file_path)
    pageCount = opened_pdf_to_be_copied.pageCount

    new_pdf = fitz.open()

    #iterate_pdf_to_be_copied_pages = PdfFileReader(file_path) 
    #for page in range(iterate_pdf_to_be_copied_pages.getNumPages()):
    hasPage = False
    for page in range(len(pages)):
        _page = pages[page]

        if _page != None and _page != "":
            from_page = -1
            to_page = -1

            if _page.find("-") > -1:
                mult_page = _page.split("-")
                from_page = int(mult_page[0]) - 1
                to_page = int(mult_page[1]) -1
            else:
                from_page = int(_page) -1

            #print("copying page: ", n_page)

            if to_page <= 0:
                to_page = from_page
                
            if from_page >= 0 and to_page >= from_page and from_page <= pageCount -1:
                hasPage = True
                new_pdf.insertPDF(
                    opened_pdf_to_be_copied,          # cannot be the same object as doc1
                    from_page=from_page,   # first page to copy, default: 0
                    to_page=to_page,     # last page to copy, default: last page
                    links=True,    # also copy links
                    annots=True,   # also copy annotations
                )
    try:
        if hasPage:
            try:
                #print("Saving pdf to location: ", new_pdf_path)
                new_pdf.save(new_pdf_path)                
            except Exception as e:
                raise Exception("Erro ao exportar pdf: " + str(e))
        else:
            raise Exception("O arquivo não contém a(s) página(s) informada(s) para exportação!")
    except Exception as x:
        try:
            new_pdf.close()
            opened_pdf_to_be_copied.close()
        except Exception as ex:
            raise Exception("Erro ao salvar o pdf. {0} - {1}".format(str(x), str(ex)))
        
        raise x
    
    ####### check if file exists and delete sample #######
    #
    # if os.path.isfile(new_pdf_path) == True:
    #     os.remove(new_pdf_path)
    #
    ######################################################

    #print("Success!")
    return new_file_path

def DownloadPdfPages(file_path, file_name, user_id):
    #print("copying pdf")

    pages = pages.split(',') #javascript validation accepts only string like: 1,2,3-10,78

    #unic = secrets.token_urlsafe(16) #change to user_id to create only one pdf export by user
    sulfix = "_exportado_" + str(user_id) +  ".pdf"
    new_file_path = "/data/temp/" + file_name.replace(".pdf", sulfix)

    #################################
    # AMBIENTE #

    # windows path - localhost
    #new_pdf_path = file_path.replace("\\data\\", "\\data\\temp\\").replace(".pdf", sulfix)

    # linux path - homolog
    new_pdf_path = file_path.replace("/data/", "/data/temp/").replace(".pdf", sulfix)
    ################################

    opened_pdf_to_be_copied = fitz.open(file_path)
    pageCount = opened_pdf_to_be_copied.pageCount

    new_pdf = fitz.open()

    #iterate_pdf_to_be_copied_pages = PdfFileReader(file_path) 
    #for page in range(iterate_pdf_to_be_copied_pages.getNumPages()):
    hasPage = False
    for page in range(len(pages)):
        _page = pages[page]

        if _page != None and _page != "":
            from_page = -1
            to_page = -1

            if _page.find("-") > -1:
                mult_page = _page.split("-")
                from_page = int(mult_page[0]) - 1
                to_page = int(mult_page[1]) -1
            else:
                from_page = int(_page) -1

            #print("copying page: ", n_page)

            if to_page <= 0:
                to_page = from_page
                
            if from_page >= 0 and to_page >= from_page and from_page <= pageCount -1:
                hasPage = True
                new_pdf.insertPDF(
                    opened_pdf_to_be_copied,          # cannot be the same object as doc1
                    from_page=from_page,   # first page to copy, default: 0
                    to_page=to_page,     # last page to copy, default: last page
                    links=True,    # also copy links
                    annots=True,   # also copy annotations
                )
    try:
        if hasPage:
            try:
                #print("Saving pdf to location: ", new_pdf_path)
                new_pdf.save(new_pdf_path)                
            except Exception as e:
                raise Exception("Erro ao exportar pdf: " + str(e))
        else:
            raise Exception("O arquivo não contém a(s) página(s) informada(s) para exportação!")
    except Exception as x:
        try:
            new_pdf.close()
            opened_pdf_to_be_copied.close()
        except Exception as ex:
            raise Exception("Erro ao salvar o pdf. {0} - {1}".format(str(x), str(ex)))
        
        raise x
    
    ####### check if file exists and delete sample #######
    #
    # if os.path.isfile(new_pdf_path) == True:
    #     os.remove(new_pdf_path)
    #
    ######################################################

    #print("Success!")
    return new_file_path
    
