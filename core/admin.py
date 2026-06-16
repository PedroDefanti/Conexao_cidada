from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import Usuario, ONG, Categoria, Inscricao, Doacao


# ─── USUÁRIO ─────────────────────────────────────────────────────────────────
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display  = ('email', 'first_name', 'tipo', 'nome_organizacao', 'cnpj', 'criado_em', 'is_active')
    list_filter   = ('tipo', 'is_active', 'criado_em')
    search_fields = ('email', 'first_name', 'nome_organizacao', 'cnpj')
    ordering      = ('-criado_em',)

    fieldsets = UserAdmin.fieldsets + (
        ('Dados adicionais', {
            'fields': ('tipo', 'cnpj', 'nome_organizacao', 'foto_perfil'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados adicionais', {
            'fields': ('tipo', 'cnpj', 'nome_organizacao'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('criado_em', 'atualizado_em')
        return ()


# ─── CATEGORIA ────────────────────────────────────────────────────────────────
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display  = ('nome', 'slug', 'criada_em')
    search_fields = ('nome',)
    prepopulated_fields = {'slug': ('nome',)}


# ─── ONG ─────────────────────────────────────────────────────────────────────
class InscricaoInline(admin.TabularInline):
    model  = Inscricao
    extra  = 0
    fields = ('usuario', 'status', 'disponibilidade', 'criada_em')
    readonly_fields = ('criada_em',)
    show_change_link = True


class DoacaoInline(admin.TabularInline):
    model  = Doacao
    extra  = 0
    fields = ('tipo', 'descricao', 'urgente', 'ativa', 'criada_em')
    readonly_fields = ('criada_em',)


@admin.register(ONG)
class ONGAdmin(admin.ModelAdmin):
    list_display   = ('emoji_nome', 'responsavel', 'localizacao', 'urgente', 'ativa', 'criada_em')
    list_filter    = ('ativa', 'urgente', 'categorias')
    search_fields  = ('nome', 'descricao', 'localizacao', 'responsavel__email')
    filter_horizontal = ('categorias',)
    readonly_fields   = ('criada_em', 'atualizada_em')
    inlines = [InscricaoInline, DoacaoInline]

    @admin.display(description='ONG')
    def emoji_nome(self, obj):
        return f'{obj.emoji} {obj.nome}'

    actions = ['ativar_ongs', 'desativar_ongs', 'marcar_urgente', 'desmarcar_urgente']

    @admin.action(description='Ativar ONGs selecionadas')
    def ativar_ongs(self, request, queryset):
        updated = queryset.update(ativa=True)
        self.message_user(request, f'{updated} ONG(s) ativada(s).')

    @admin.action(description='Desativar ONGs selecionadas')
    def desativar_ongs(self, request, queryset):
        updated = queryset.update(ativa=False)
        self.message_user(request, f'{updated} ONG(s) desativada(s).')

    @admin.action(description='Marcar como urgente')
    def marcar_urgente(self, request, queryset):
        updated = queryset.update(urgente=True)
        self.message_user(request, f'{updated} ONG(s) marcada(s) como urgente.')

    @admin.action(description='Remover urgência')
    def desmarcar_urgente(self, request, queryset):
        updated = queryset.update(urgente=False)
        self.message_user(request, f'{updated} ONG(s) com urgência removida.')


# ─── INSCRIÇÃO ────────────────────────────────────────────────────────────────
@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display   = ('usuario', 'ong', 'status_badge', 'disponibilidade', 'criada_em')
    list_filter    = ('status', 'criada_em', 'ong')
    search_fields  = ('usuario__email', 'usuario__first_name', 'ong__nome', 'mensagem')
    readonly_fields = ('criada_em',)


    @admin.display(description='Status')
    def status_badge(self, obj):
        cores = {'pendente': '#f59e0b', 'aprovada': '#10b981', 'rejeitada': '#ef4444'}
        cor = cores.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:9px;font-size:.8rem;">{}</span>',
            cor, obj.get_status_display()
        )

    actions = ['aprovar_inscricoes', 'rejeitar_inscricoes', 'colocar_pendente']

    @admin.action(description='Aprovar inscrições selecionadas')
    def aprovar_inscricoes(self, request, queryset):
        updated = queryset.update(status='aprovada')
        self.message_user(request, f'{updated} inscrição(ões) aprovada(s).')

    @admin.action(description='Rejeitar inscrições selecionadas')
    def rejeitar_inscricoes(self, request, queryset):
        updated = queryset.update(status='rejeitada')
        self.message_user(request, f'{updated} inscrição(ões) rejeitada(s).')

    @admin.action(description='Marcar como pendente')
    def colocar_pendente(self, request, queryset):
        updated = queryset.update(status='pendente')
        self.message_user(request, f'{updated} inscrição(ões) marcada(s) como pendente.')


# ─── DOAÇÃO ───────────────────────────────────────────────────────────────────
@admin.register(Doacao)
class DoacaoAdmin(admin.ModelAdmin):
    list_display   = ('get_tipo_display', 'ong', 'urgente', 'ativa', 'criada_em')
    list_filter    = ('tipo', 'urgente', 'ativa', 'criada_em')
    search_fields  = ('ong__nome', 'descricao')
    readonly_fields = ('criada_em',)

    actions = ['ativar_doacoes', 'desativar_doacoes']

    @admin.action(description='Ativar doações selecionadas')
    def ativar_doacoes(self, request, queryset):
        updated = queryset.update(ativa=True)
        self.message_user(request, f'{updated} doação(ões) ativada(s).')

    @admin.action(description='Desativar doações selecionadas')
    def desativar_doacoes(self, request, queryset):
        updated = queryset.update(ativa=False)
        self.message_user(request, f'{updated} doação(ões) desativada(s).')