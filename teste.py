import fitz
from tika import parser
import re
from conn_doccano_ia import GetBlackList

file_path = "C:\\Users\\Trabalho\\2020-05-25-DiarioOficialdaUniaoSecao1-20.pdf"

Black_List = GetBlackList()

content =  parser.from_file(file_path)

text = content['content']

text = str(text)

for word in Black_List:
    text = text.replace(word[0], '')

print(text)

