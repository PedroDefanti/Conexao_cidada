from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator


class Usuario(AbstractUser):
    TIPO_CHOICES = [('voluntario', 'Voluntário'), ('ong', 'ONG')]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='voluntario')
    cnpj = models.CharField(
        max_length=18, blank=True,
        validators=[RegexValidator(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', 'CNPJ inválido')],
        help_text='Somente para ONGs'
    )
    nome_organizacao = models.CharField(max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.username


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ONG(models.Model):
    responsavel = models.ForeignKey(
        Usuario, on_delete=models.CASCADE,
        related_name='ongs', null=True, blank=True
    )
    nome = models.CharField(max_length=200)
    descricao = models.TextField(max_length=1000)
    localizacao = models.CharField(max_length=200)
    categorias = models.ManyToManyField(Categoria, related_name='ongs')
    emoji = models.CharField(max_length=10, default='🌟')
    ativa = models.BooleanField(default=True)
    urgente = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ONG'
        verbose_name_plural = 'ONGs'
        ordering = ['-criada_em']

    def __str__(self):
        return self.nome


class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='inscricoes')
    ong = models.ForeignKey(ONG, on_delete=models.CASCADE, related_name='inscricoes')
    mensagem = models.TextField(max_length=500, blank=True)
    disponibilidade = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        unique_together = ['usuario', 'ong']
        ordering = ['-criada_em']

    def __str__(self):
        return f'{self.usuario} → {self.ong}'
