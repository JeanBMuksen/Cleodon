from django.db import models
from django.contrib.auth.models import User

class Arquivo(models.Model):
    id_arquivo = models.IntegerField(null=False, unique=True, serialize=True, primary_key=True)
    data = models.DateField(auto_now=True)
    sessao = models.IntegerField()

class Usuario(models.Model):
    nome = models.CharField(null=False, max_length=200)
    email = models.EmailField(max_length=200, unique=True, null=False)
    setor = models.CharField(null=False, max_length=50)
    ramal = models.IntegerField()
    id_user = models.IntegerField(null=False, unique=True, serialize=True, primary_key=True, auto_created=True)
    

class Notificacao(models.Model):
    id_notificacao = models.IntegerField(null=False, unique=True, serialize=True, primary_key=True)
    data = models.DateField(auto_now=True)
    tipo = models.BooleanField(null=False)


def _str_(self):
    return str(self.id)


    
