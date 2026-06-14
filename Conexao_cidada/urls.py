from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('inscricao/<int:ong_pk>/', views.inscricao_view, name='inscricao'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    
]