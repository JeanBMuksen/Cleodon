from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfform
from reportlab.lib.colors import red
import datetime

file_name = ''    

def create_pdf():
    #file_name = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d_%H-%M-%S')+ ‘sample.pdf’
    _canvas = canvas.Canvas(file_name)
    _form = _canvas.acroForm
    _canvas.drawString(10, 600, 'Lorem isupum sentence')
    _form.checkbox(name='x', tooltip='Field cb2', x=200, y=600, buttonStyle='cross', borderWidth=2, forceBorder=True)
    _canvas.save()
    return file_name

#js action
from pdfrw.objects.pdfdict import PdfDict
from pdfrw.objects.pdfname import PdfName

def make_js_action(js):
    action = PdfDict()
    action.S = PdfName.JavaScript
    action.JS = js
    return action

#append js to pdf
from pdfrw import PdfReader, PdfWriter
from pdfrw.objects.pdfstring import PdfString
from pdfrw.objects.pdfdict import PdfDict
from pdfrw.objects.pdfarray import PdfArray

def append_js_to_pdf(file_name):
    pdf_writer = PdfWriter()
    pdf_reader = PdfReader(file_name)
    try:
        js = open('').read()
    except:
        js = "app.alert('Ops! Erro ao inserir o javascript no PDF.');"
    for page_index in pdf_reader.pages:
        page = page_index
        page.Type = PdfName.Page
        for field in page.Annots or []:
            if 'x' in field.get('/T'):
                #print(field)
                field.update(PdfDict(AA=PdfDict(Bl=make_js_action(js))))
        page.AA = PdfDict()
        page.AA.O = make_js_action(js)
        pdf_writer.addpage(page)  
        pdf_writer.write(file_name)

#create pdf and add js to it
file_name = create_pdf()
javascript_added = append_js_to_pdf(file_name)

# from reportlab import platypus
# from  reportlab.lib.styles import ParagraphStyle as PS
# from reportlab.platypus import SimpleDocTemplate
