import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import ONG, Categoria, Inscricao, Doacao
from .forms import (
    LoginForm, CadastroVoluntarioForm, CadastroONGForm,
    InscricaoForm, DoacaoForm, FotoPerfilForm, EditarONGForm,
)

logger = logging.getLogger('django.security')


def _get_ou_criar_ong(user):
    """
    Busca a ONG vinculada ao usuário.
    Se não existir, cria uma nova — usando nome_organizacao do Usuario,
    que é preenchido no cadastro e não o e-mail.
    """
    ong, criada = ONG.objects.get_or_create(
        responsavel=user,
        defaults={
            'nome':      user.nome_organizacao or user.email,
            'descricao': '',          # vazio propositalmente — ONG preenche depois
            'localizacao': '',
            'emoji':     '🌟',
        }
    )
    return ong


def _enviar_email_status(inscricao):
    """Envia e-mail ao voluntário quando o status da inscrição muda."""
    status_labels = {
        'aprovada':  ('✅ Inscrição aprovada!',       'aprovada'),
        'rejeitada': ('❌ Inscrição não aprovada',    'rejeitada'),
    }
    if inscricao.status not in status_labels:
        return
    assunto, status_texto = status_labels[inscricao.status]
    corpo = (
        f'Olá, {inscricao.usuario.first_name or inscricao.usuario.email}!\n\n'
        f'Sua inscrição em "{inscricao.ong.nome}" foi {status_texto}.\n\n'
        f'Acesse a plataforma para mais informações.\n\n'
        f'— Equipe Conexão Cidadã'
    )
    try:
        send_mail(
            subject=assunto,
            message=corpo,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@conexaocidada.com.br'),
            recipient_list=[inscricao.usuario.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f'Falha ao enviar e-mail para {inscricao.usuario.email}: {e}')


# ─── INDEX ────────────────────────────────────────────────────────────────────
@never_cache
def index(request):
    ongs_qs = ONG.objects.filter(ativa=True).prefetch_related('categorias')
    categorias = Categoria.objects.all()
    total_ongs = ONG.objects.filter(ativa=True).count()

    paginator = Paginator(ongs_qs, 9)
    ongs = paginator.get_page(request.GET.get('page'))

    ong_do_usuario = None
    if request.user.is_authenticated and request.user.tipo == 'ong':
        ong_do_usuario = ONG.objects.filter(responsavel=request.user).first()

    return render(request, 'core/index.html', {
        'ongs':         ongs,
        'categorias':   categorias,
        'total_ongs':   total_ongs,
        'ong_do_usuario': ong_do_usuario,
    })


# ─── LOGIN ────────────────────────────────────────────────────────────────────
@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('index')
        else:
            logger.warning(f'Login falhou - IP: {request.META.get("REMOTE_ADDR")}')
    return render(request, 'core/login.html', {'form': form, 'next': request.GET.get('next', '')})


# ─── CADASTRO ─────────────────────────────────────────────────────────────────
@never_cache
@require_http_methods(["GET", "POST"])
def cadastro_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    tipo = request.POST.get('tipo_cadastro', 'voluntario')
    form_vol = CadastroVoluntarioForm(request.POST if tipo == 'voluntario' else None)
    form_ong = CadastroONGForm(request.POST if tipo == 'ong' else None)
    if request.method == 'POST':
        form = form_vol if tipo == 'voluntario' else form_ong
        if form.is_valid():
            user = form.save()
            if user.tipo == 'ong':
                _get_ou_criar_ong(user)
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo(a)! 🎉')
            return redirect('index')
    return render(request, 'core/cadastro.html', {
        'form_vol': form_vol,
        'form_ong': form_ong,
        'tipo': tipo,
    })


# ─── LOGOUT ───────────────────────────────────────────────────────────────────
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('login')


# ─── DETALHE DA ONG ───────────────────────────────────────────────────────────
@never_cache
def detalhe_ong_view(request, ong_pk):
    ong = get_object_or_404(ONG, pk=ong_pk, ativa=True)
    doacoes = Doacao.objects.filter(ong=ong, ativa=True).order_by('-urgente', '-criada_em')
    inscricoes_count = Inscricao.objects.filter(ong=ong).count()

    ja_inscrito = False
    if request.user.is_authenticated:
        ja_inscrito = Inscricao.objects.filter(usuario=request.user, ong=ong).exists()

    return render(request, 'core/detalhe_ong.html', {
        'ong':              ong,
        'doacoes':          doacoes,
        'inscricoes_count': inscricoes_count,
        'ja_inscrito':      ja_inscrito,
    })


# ─── INSCRIÇÃO ────────────────────────────────────────────────────────────────
@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def inscricao_view(request, ong_pk):
    ong = get_object_or_404(ONG, pk=ong_pk, ativa=True)

    if Inscricao.objects.filter(usuario=request.user, ong=ong).exists():
        messages.warning(request, f'Você já se inscreveu em {ong.nome}.')
        return redirect('index')

    form = InscricaoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        Inscricao.objects.create(
            usuario=request.user,
            ong=ong,
            mensagem=form.cleaned_data.get('mensagem', ''),
            disponibilidade=form.get_disponibilidade_str(),
        )
        messages.success(request, f'Inscrição em {ong.nome} enviada! 🎉')
        return redirect('perfil')

    return render(request, 'core/inscricao.html', {'form': form, 'ong': ong})


# ─── CANCELAR INSCRIÇÃO ───────────────────────────────────────────────────────
@login_required
@require_POST
def cancelar_inscricao_view(request, inscricao_pk):
    inscricao = get_object_or_404(Inscricao, pk=inscricao_pk, usuario=request.user)
    if inscricao.status == 'aprovada':
        messages.error(request, 'Não é possível cancelar uma inscrição já aprovada.')
        return redirect('perfil')
    nome_ong = inscricao.ong.nome
    inscricao.delete()
    messages.success(request, f'Inscrição em {nome_ong} cancelada.')
    return redirect('perfil')


# ─── GERENCIAR INSCRIÇÕES (ONG) ───────────────────────────────────────────────
@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def gerenciar_inscricoes_view(request):
    if request.user.tipo != 'ong':
        messages.error(request, 'Acesso restrito a ONGs.')
        return redirect('index')

    ong = get_object_or_404(ONG, responsavel=request.user)

    if request.method == 'POST':
        inscricao_pk = request.POST.get('inscricao_pk')
        novo_status  = request.POST.get('status')
        if novo_status not in ('aprovada', 'rejeitada', 'pendente'):
            messages.error(request, 'Status inválido.')
            return redirect('gerenciar_inscricoes')

        inscricao = get_object_or_404(Inscricao, pk=inscricao_pk, ong=ong)
        inscricao.status = novo_status
        inscricao.save()

        if novo_status in ('aprovada', 'rejeitada'):
            _enviar_email_status(inscricao)

        labels = {
            'aprovada':  'aprovada ✅',
            'rejeitada': 'rejeitada ❌',
            'pendente':  'marcada como pendente ⏳',
        }
        messages.success(
            request,
            f'Inscrição de {inscricao.usuario.first_name or inscricao.usuario.email} {labels[novo_status]}.'
        )
        return redirect('gerenciar_inscricoes')

    status_filtro = request.GET.get('status', '')
    inscricoes_qs = Inscricao.objects.filter(ong=ong).select_related('usuario').order_by('-criada_em')
    if status_filtro in ('pendente', 'aprovada', 'rejeitada'):
        inscricoes_qs = inscricoes_qs.filter(status=status_filtro)

    paginator  = Paginator(inscricoes_qs, 10)
    inscricoes = paginator.get_page(request.GET.get('page'))

    contagens = {
        'total':     Inscricao.objects.filter(ong=ong).count(),
        'pendente':  Inscricao.objects.filter(ong=ong, status='pendente').count(),
        'aprovada':  Inscricao.objects.filter(ong=ong, status='aprovada').count(),
        'rejeitada': Inscricao.objects.filter(ong=ong, status='rejeitada').count(),
    }

    return render(request, 'core/gerenciar_inscricoes.html', {
        'inscricoes':    inscricoes,
        'ong':           ong,
        'status_filtro': status_filtro,
        'contagens':     contagens,
    })


# ─── PERFIL ───────────────────────────────────────────────────────────────────
@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def perfil_view(request):
    if request.method == 'POST' and request.FILES.get('foto_perfil'):
        foto_form = FotoPerfilForm(request.POST, request.FILES, instance=request.user)
        if foto_form.is_valid():
            foto_form.save()
            messages.success(request, 'Foto atualizada! 📸')
            return redirect('perfil')
    else:
        foto_form = FotoPerfilForm(instance=request.user)

    inscricoes_qs = Inscricao.objects.filter(
        usuario=request.user
    ).select_related('ong').order_by('-criada_em')

    paginator  = Paginator(inscricoes_qs, 5)
    inscricoes = paginator.get_page(request.GET.get('page'))

    doacoes_ong            = None
    doacoes_para_voluntario = None
    if request.user.tipo == 'ong':
        ong_user   = ONG.objects.filter(responsavel=request.user).first()
        doacoes_ong = Doacao.objects.filter(ong=ong_user, ativa=True) if ong_user else []
    else:
        doacoes_para_voluntario = Doacao.objects.filter(
            ativa=True
        ).select_related('ong').order_by('-urgente', '-criada_em')[:6]

    return render(request, 'core/perfil.html', {
        'inscricoes':             inscricoes,
        'foto_form':              foto_form,
        'doacoes_ong':            doacoes_ong,
        'doacoes_para_voluntario': doacoes_para_voluntario,
    })


# ─── EDITAR ONG ───────────────────────────────────────────────────────────────
@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def editar_ong_view(request):
    if request.user.tipo != 'ong':
        messages.error(request, 'Acesso restrito a ONGs.')
        return redirect('index')

    # ── Bug 1 corrigido: busca a ONG pelo responsavel; se não existe cria ──
    ong = _get_ou_criar_ong(request.user)

    form = EditarONGForm(
        request.POST or None,
        request.FILES or None,
        instance=ong,
    )

    if request.method == 'POST' and form.is_valid():
        ong_salva = form.save()
        # Mantém nome_organizacao do Usuario sincronizado
        request.user.nome_organizacao = ong_salva.nome
        request.user.save(update_fields=['nome_organizacao'])
        messages.success(request, 'Perfil da ONG atualizado! ✅')
        return redirect('perfil')

    return render(request, 'core/editar_ong.html', {'form': form, 'ong': ong})


# ─── DOAÇÕES ─────────────────────────────────────────────────────────────────
@never_cache
@login_required
def doacoes_view(request):
    tipo_filtro = request.GET.get('tipo', '')
    doacoes_qs  = Doacao.objects.filter(ativa=True).select_related('ong').order_by('-urgente', '-criada_em')
    if tipo_filtro:
        doacoes_qs = doacoes_qs.filter(tipo=tipo_filtro)

    paginator = Paginator(doacoes_qs, 9)
    doacoes   = paginator.get_page(request.GET.get('page'))

    tipos         = Doacao.TIPO_CHOICES
    ong_do_usuario = (
        ONG.objects.filter(responsavel=request.user).first()
        if request.user.tipo == 'ong' else None
    )
    return render(request, 'core/doacoes.html', {
        'doacoes':       doacoes,
        'tipos':         tipos,
        'tipo_filtro':   tipo_filtro,
        'ong_do_usuario': ong_do_usuario,
    })


# ─── PUBLICAR DOAÇÃO ──────────────────────────────────────────────────────────
@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def publicar_doacao_view(request):
    if request.user.tipo != 'ong':
        messages.error(request, 'Apenas ONGs podem publicar necessidades de doação.')
        return redirect('doacoes')

    # ── Bug 2 corrigido: usa _get_ou_criar_ong que agora cria com nome correto ──
    ong_do_usuario = _get_ou_criar_ong(request.user)

    form = DoacaoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        doacao     = form.save(commit=False)
        doacao.ong = ong_do_usuario
        doacao.save()
        messages.success(request, 'Necessidade de doação publicada! ✅')
        return redirect('doacoes')

    return render(request, 'core/publicar_doacao.html', {'form': form, 'ong': ong_do_usuario})


# ─── TOGGLE DOAÇÃO (ativar/desativar) ────────────────────────────────────────
@login_required
@require_POST
def toggle_doacao_view(request, doacao_pk):
    if request.user.tipo != 'ong':
        messages.error(request, 'Acesso restrito a ONGs.')
        return redirect('doacoes')

    ong    = get_object_or_404(ONG, responsavel=request.user)
    doacao = get_object_or_404(Doacao, pk=doacao_pk, ong=ong)
    doacao.ativa = not doacao.ativa
    doacao.save(update_fields=['ativa'])

    status_msg = 'reativada ✅' if doacao.ativa else 'encerrada ✅'
    messages.success(request, f'Necessidade de {doacao.get_tipo_display()} {status_msg}.')
    return redirect(request.POST.get('next', 'perfil'))