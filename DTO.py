from django.db import models
from django import forms
import enum

class LogType(enum.Enum):
    success = 1
    error = 2
    warning = 3
    error_email = 4
    info = 5


class SentenceAnnotation():
    document_id = models.IntegerField() # sentence
    document_text = models.TextField()
    label_id = models.IntegerField() # annotation
    label_text = models.TextField(max_length=100)
    start_offset = models.IntegerField() #start offset of annotation on sentence
    end_offset = models.IntegerField() ##end offset of annotation on sentence

class Publications():
    publication_marcada = models.TextField() # has marcation
    publication_text = models.TextField() # Name of publication
    publication_active = models.IntegerField() # Status of publication
    publication_date = models.TextField() # Date of publication
    publication_name = models.TextField() #file_name of publication
    publication_id = models.IntegerField()
    publication_pdf_has_annotation = models.BooleanField()


class Escolha():
    opcao = models.IntegerField()