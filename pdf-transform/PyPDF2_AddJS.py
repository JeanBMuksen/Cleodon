from PyPDF2 import PdfFileWriter, PdfFileReader

output = PdfFileWriter()
ipdf = PdfFileReader(open('', 'rb'))

for i in range(ipdf.getNumPages()):
	page = ipdf.getPage(i)
	output.addPage(page)

with open('', 'wb') as f:
	output.addJS("this.print({bUI:true,bSilent:false,bShrinkToFit:true});")
	output.write(f)