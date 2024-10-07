import fitz

label = ["Art", "DEFIRO", "ICMS", "RECEITA FEDERAL", "ADO"]
label_sentences = []

filename = ''

pdf_document = fitz.open(filename)


color = {"stroke": (1, 0.52, 0)}
color2 = {"stroke": (0, 1, 0)}


# MARCADOR DE SENTENÇAS #
def marcador_sentence(pdf_document, label_sentences):
	for i in range(len(pdf_document)):
		page = pdf_document[i]
		for k in range(len(label_sentences)):
			sentence_adicionada = label_sentences[k]
			sentence = page.searchFor(sentence_adicionada)
			for inst in sentence:
				marcador = page.addHighlightAnnot(inst)



# MARCADOR DE ENTIDADES #
def marcador_label(pdf_document, label):
	for i in range(len(pdf_document)):
		page = pdf_document[i]
		for k in range(len(label)):
			palavra_adicionada = label[k]
			palavra = page.searchFor(palavra_adicionada)
			for inst in palavra:
				marcador = page.addHighlightAnnot(inst)
				marcador.update()	


marcador_label(pdf_document, label)

pdf_document.save("")








		









