from django.urls import path
from . import views
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf.urls import url


urlpatterns = [

    path('', views.home, name='home'),

    path('login/', views.login_user, name='Login'),

    path('home/', views.submit_login),

    path('logout/', views.logout_user),
    
    path('lista/', views.carrega_lista),

    path('lista-download/', views.carrega_lista_download),
    
    path('LoadPdfAnnotation/', views.LoadPdfAnnotation),

    path('downloadPDF/', views.downloadPDF),

    path('editLabel/', views.editLabel),

    path('exportPDF/', views.exportPDF),

    path('redirectDoccano/', views.redirectDoccano),

] 