from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, ONG, Categoria, Inscricao

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'tipo', 'is_active', 'criado_em']
    list_filter = ['tipo', 'is_active']
    search_fields = ['email', 'first_name', 'nome_organizacao']
    ordering = ['-criado_em']
    fieldsets = UserAdmin.fieldsets + (
        ('Dados extras', {'fields': ('tipo', 'cnpj', 'nome_organizacao')}),
    )

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'slug']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(ONG)
class ONGAdmin(admin.ModelAdmin):
    list_display = ['nome', 'localizacao', 'ativa', 'urgente', 'criada_em']
    list_filter = ['ativa', 'urgente', 'categorias']
    search_fields = ['nome', 'descricao', 'localizacao']
    filter_horizontal = ['categorias']

@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ong', 'status', 'criada_em']
    list_filter = ['status']
    search_fields = ['usuario__email', 'ong__nome']
    list_editable = ['status']
