from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class Usuario(AbstractUser):
    TIPO_CHOICES = [('voluntario', 'Voluntário'), ('ong', 'ONG')]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='voluntario')
    cnpj = models.CharField(
        max_length=18, blank=True,
        validators=[RegexValidator(r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$', 'CNPJ inválido')],
        help_text='Somente para ONGs'
    )
    nome_organizacao = models.CharField(max_length=200, blank=True)
    foto_perfil = models.ImageField(
        upload_to='fotos_perfil/',
        blank=True, null=True,
        verbose_name='Foto de perfil'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        if self.tipo == 'ong':
            # ── Bug 3 corrigido: exibe nome_organizacao, não o e-mail ──
            return self.nome_organizacao or self.email
        return self.first_name or self.username

    @property
    def nome_exibicao(self):
        """Nome exibido na nav e no hero."""
        if self.tipo == 'ong':
            # ── Bug 3 corrigido: exibe nome_organizacao, não o e-mail ──
            return self.nome_organizacao or self.email
        return self.first_name or self.username


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


class Doacao(models.Model):
    TIPO_CHOICES = [
        ('alimento',   'Alimentos'),
        ('roupa',      'Roupas e Calçados'),
        ('movel',      'Móveis e Eletrodomésticos'),
        ('brinquedo',  'Brinquedos'),
        ('livro',      'Livros e Material Escolar'),
        ('higiene',    'Higiene e Limpeza'),
        ('remedio',    'Remédios'),
        ('dinheiro',   'Dinheiro / PIX'),
        ('outro',      'Outro'),
    ]
    ong = models.ForeignKey(ONG, on_delete=models.CASCADE, related_name='doacoes')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descricao = models.TextField(max_length=500, help_text='Detalhe o que precisa exatamente')
    urgente = models.BooleanField(default=False)
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Doação'
        verbose_name_plural = 'Doações'
        ordering = ['-urgente', '-criada_em']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.ong.nome}'


class Inscricao(models.Model):
    STATUS_CHOICES = [
        ('pendente',  'Pendente'),
        ('aprovada',  'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='inscricoes')
    ong = models.ForeignKey(ONG, on_delete=models.CASCADE, related_name='inscricoes')
    mensagem = models.TextField(max_length=500, blank=True)
    # ── Bug 4: disponibilidade agora armazena JSON-like string com dias+horários+tipo ──
    disponibilidade = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        unique_together = ['usuario', 'ong']
        ordering = ['-criada_em']

    def __str__(self):
        return f'{self.usuario} → {self.ong}'