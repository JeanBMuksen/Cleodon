from reportlab.pdfgen import canvas
from reportlab.lib.colors import yellow
import datetime

file_name = ''

def create_pdf():
    #file_name = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d_%H-%M-%S')+ ‘sample.pdf’
    your_canvas = canvas.Canvas(file_name)
    your_form = your_canvas.acroForm
    your_canvas.drawString(25, 780, 'Calculations')
    your_form.textfield(x=25, y=700, borderStyle='underlined', width=50, fillColor=yellow, fontSize=12, height=20, name='price')
    your_form.textfield(x=200, y=700, borderStyle='underlined', width=50, fillColor=yellow, fontSize=12, height=20, name='quantity') 
    your_form.textfield(x=375, y=700, borderStyle='underlined', width=50, fillColor=yellow, fontSize=12, height=20, name='total')
    your_canvas.save()
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
        for field in page.Annots:
            if 'price' in field.get('/T') or 'quantity' in field.get('/T'):
                field.update(PdfDict(AA=PdfDict(Bl=make_js_action(js))))
        page.AA = PdfDict()
        page.AA.O = make_js_action(js)
        pdf_writer.addpage(page)  
        pdf_writer.write(file_name)



#create pdf and add js to it
file_name = create_pdf()
javascript_added = append_js_to_pdf(file_name)