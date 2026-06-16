from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/',                              admin.site.urls),
    path('',                                    views.index,                    name='index'),
    path('login/',                              views.login_view,               name='login'),
    path('logout/',                             views.logout_view,              name='logout'),
    path('cadastro/',                           views.cadastro_view,            name='cadastro'),

    # Perfil e edição
    path('perfil/',                             views.perfil_view,              name='perfil'),
    path('perfil/editar-ong/',                  views.editar_ong_view,          name='editar_ong'),

    # ONGs
    path('ong/<int:ong_pk>/',                   views.detalhe_ong_view,         name='detalhe_ong'),
    path('inscricao/<int:ong_pk>/',             views.inscricao_view,           name='inscricao'),
    path('inscricao/<int:inscricao_pk>/cancelar/', views.cancelar_inscricao_view, name='cancelar_inscricao'),

    # Gerenciamento de inscrições (ONG)
    path('gerenciar-inscricoes/',               views.gerenciar_inscricoes_view, name='gerenciar_inscricoes'),

    # Doações
    path('doacoes/',                            views.doacoes_view,             name='doacoes'),
    path('doacoes/publicar/',                   views.publicar_doacao_view,     name='publicar_doacao'),
    path('doacoes/<int:doacao_pk>/toggle/',     views.toggle_doacao_view,       name='toggle_doacao'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)