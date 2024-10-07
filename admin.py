from django.contrib import admin
from .models import Usuario,Arquivo


@admin.register(Usuario)

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['id_user', 'nome', 'setor']

