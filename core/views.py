import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from .models import ONG, Categoria, Inscricao
from .forms import LoginForm, CadastroVoluntarioForm, CadastroONGForm, InscricaoForm

logger = logging.getLogger('django.security')

@never_cache
def index(request):
    ongs = ONG.objects.filter(ativa=True).prefetch_related('categorias')
    categorias = Categoria.objects.all()
    return render(request, 'core/index.html', {'ongs': ongs, 'categorias': categorias})

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
            next_url = request.GET.get('next') or request.POST.get('next') or 'index'
            return redirect(next_url)
        else:
            logger.warning(f'Login falhou - IP: {request.META.get("REMOTE_ADDR")}')
    return render(request, 'core/login.html', {'form': form, 'next': request.GET.get('next', '')})

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
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo(a)! 🎉')
            return redirect('index')
    return render(request, 'core/cadastro.html', {'form_vol': form_vol, 'form_ong': form_ong, 'tipo': tipo})

@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu da sua conta.')
    return redirect('login')

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
        inscricao = form.save(commit=False)
        inscricao.usuario = request.user
        inscricao.ong = ong
        inscricao.save()
        messages.success(request, f'Inscrição em {ong.nome} enviada! 🎉')
        return redirect('perfil')
    return render(request, 'core/inscricao.html', {'form': form, 'ong': ong})

@never_cache
@login_required
def perfil_view(request):
    inscricoes = Inscricao.objects.filter(usuario=request.user).select_related('ong').order_by('-criada_em')
    return render(request, 'core/perfil.html', {'inscricoes': inscricoes})
