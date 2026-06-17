import re
import bleach
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import Usuario, Inscricao, Doacao, ONG, Categoria

ALLOWED_TAGS = []


def sanitize(value):
    return bleach.clean(value, tags=ALLOWED_TAGS, strip=True).strip()


# ─── Validação real de CNPJ ───────────────────────────────────────────────────
def validar_cnpj(cnpj_raw):
    cnpj = re.sub(r'\D', '', cnpj_raw)
    if len(cnpj) != 14:
        raise ValidationError('CNPJ deve ter 14 dígitos.')
    if cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')

    def calc_digito(cnpj, pesos):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    if calc_digito(cnpj, pesos1) != int(cnpj[12]):
        raise ValidationError('CNPJ inválido.')
    if calc_digito(cnpj, pesos2) != int(cnpj[13]):
        raise ValidationError('CNPJ inválido.')

    return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'


# ─── LOGIN ────────────────────────────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'placeholder': 'seu@email.com',
            'autocomplete': 'email', 'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input', 'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def clean_username(self):
        return sanitize(self.cleaned_data['username'])


# ─── CADASTRO VOLUNTÁRIO ──────────────────────────────────────────────────────
class CadastroVoluntarioForm(UserCreationForm):
    nome = forms.CharField(
        label='Nome Completo', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Como quer ser chamado?'})
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'seu@email.com'})
    )
    password1 = forms.CharField(
        label='Criar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mínimo 8 caracteres'})
    )
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Repita a senha'})
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'password1', 'password2']

    def clean_nome(self):
        nome = sanitize(self.cleaned_data['nome'])
        if len(nome) < 2:
            raise ValidationError('Nome muito curto.')
        if not re.match(r"^[A-Za-zÀ-ÿ\s'-]+$", nome):
            raise ValidationError('Nome contém caracteres inválidos.')
        return nome

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nome']
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        user.tipo = 'voluntario'
        if commit:
            user.save()
        return user


# ─── CADASTRO ONG ─────────────────────────────────────────────────────────────
class CadastroONGForm(UserCreationForm):
    nome_organizacao = forms.CharField(
        label='Nome da Organização', max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome da instituição'})
    )
    cnpj = forms.CharField(
        label='CNPJ', max_length=18,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '00.000.000/0001-00'})
    )
    email = forms.EmailField(
        label='E-mail Institucional',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'contato@ong.org'})
    )
    password1 = forms.CharField(
        label='Criar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mínimo 8 caracteres'})
    )
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Repita a senha'})
    )

    class Meta:
        model = Usuario
        fields = ['nome_organizacao', 'cnpj', 'email', 'password1', 'password2']

    def clean_cnpj(self):
        return validar_cnpj(self.cleaned_data['cnpj'])

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean_nome_organizacao(self):
        return sanitize(self.cleaned_data['nome_organizacao'])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nome_organizacao = self.cleaned_data['nome_organizacao']
        user.cnpj = self.cleaned_data['cnpj']
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        user.tipo = 'ong'
        if commit:
            user.save()
        return user


# ─── FOTO DE PERFIL ───────────────────────────────────────────────────────────
class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['foto_perfil']
        widgets = {
            'foto_perfil': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'})
        }
        labels = {'foto_perfil': 'Foto de perfil'}

    def clean_foto_perfil(self):
        foto = self.cleaned_data.get('foto_perfil')
        if foto:
            if foto.size > 2 * 1024 * 1024:
                raise ValidationError('Imagem muito grande. Máximo 2MB.')
            if not foto.content_type.startswith('image/'):
                raise ValidationError('Arquivo inválido. Envie uma imagem.')
            try:
                from PIL import Image
                img = Image.open(foto)
                img.verify()
                foto.seek(0)
            except Exception:
                raise ValidationError('Arquivo corrompido ou não é uma imagem válida.')
        return foto


# ─── INSCRIÇÃO com checkboxes ─────────────────────────────────────────────────
DIAS_CHOICES = [
    ('seg', 'Segunda-feira'),
    ('ter', 'Terça-feira'),
    ('qua', 'Quarta-feira'),
    ('qui', 'Quinta-feira'),
    ('sex', 'Sexta-feira'),
    ('sab', 'Sábado'),
    ('dom', 'Domingo'),
]

HORARIO_CHOICES = [
    ('manha', 'Manhã (8h–12h)'),
    ('tarde', 'Tarde (12h–18h)'),
    ('noite', 'Noite (18h–22h)'),
]

TIPO_AJUDA_CHOICES = [
    ('presencial', 'Presencial'),
    ('remoto',     'Remoto / Online'),
    ('ambos',      'Presencial e Remoto'),
    ('eventos',    'Apenas em eventos pontuais'),
]

TIPO_DOACAO_CHOICES = [
    ('alimento',  'Alimentos'),
    ('roupa',     'Roupas e Calçados'),
    ('movel',     'Móveis e Eletrodomésticos'),
    ('brinquedo', 'Brinquedos'),
    ('livro',     'Livros e Material Escolar'),
    ('higiene',   'Higiene e Limpeza'),
    ('remedio',   'Remédios'),
    ('dinheiro',  'Dinheiro / PIX'),
    ('outro',     'Outro'),
]


class InscricaoForm(forms.Form):
    """
    Formulário de inscrição com checkboxes estruturados.
    Não herda de ModelForm — monta 'disponibilidade' a partir de
    múltiplos campos antes de salvar no model.
    """
    dias = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Dias disponíveis',
        error_messages={'required': 'Selecione pelo menos um dia.'},
    )
    horarios = forms.MultipleChoiceField(
        choices=HORARIO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Horários disponíveis',
        error_messages={'required': 'Selecione pelo menos um horário.'},
    )
    tipo_ajuda = forms.ChoiceField(
        choices=TIPO_AJUDA_CHOICES,
        widget=forms.RadioSelect,
        label='Como prefere ajudar?',
    )
    tipos_doacao = forms.MultipleChoiceField(
        choices=TIPO_DOACAO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Com quais tipos de doação pode contribuir?',
        required=False,
    )
    mensagem = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Por que você quer participar desta causa? (opcional)',
            'rows': 3,
        }),
        label='Mensagem para a ONG (opcional)',
    )

    def clean_mensagem(self):
        return sanitize(self.cleaned_data.get('mensagem', ''))

    def get_disponibilidade_str(self):
        """Monta a string legível que vai para Inscricao.disponibilidade."""
        dias_label = dict(DIAS_CHOICES)
        hor_label  = dict(HORARIO_CHOICES)
        tip_label  = dict(TIPO_AJUDA_CHOICES)
        don_label  = dict(TIPO_DOACAO_CHOICES)

        dias    = ', '.join(dias_label[d] for d in self.cleaned_data.get('dias', []))
        horario = ', '.join(hor_label[h]  for h in self.cleaned_data.get('horarios', []))
        tipo    = tip_label.get(self.cleaned_data.get('tipo_ajuda', ''), '')
        doacoes = ', '.join(don_label[t]  for t in self.cleaned_data.get('tipos_doacao', []))

        partes = [f'Dias: {dias}', f'Horários: {horario}', f'Modo: {tipo}']
        if doacoes:
            partes.append(f'Doações: {doacoes}')
        return ' | '.join(partes)


# ─── DOAÇÃO (ONG publica o que precisa) ──────────────────────────────────────
class DoacaoForm(forms.ModelForm):
    class Meta:
        model = Doacao
        fields = ['tipo', 'descricao', 'urgente']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-input'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Descreva o que precisa (tamanho, quantidade, condição...)',
                'maxlength': 500,
            }),
            'urgente': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
        labels = {
            'tipo': 'Tipo de doação',
            'descricao': 'Descrição detalhada',
            'urgente': 'Marcar como urgente',
        }

    def clean_descricao(self):
        return sanitize(self.cleaned_data['descricao'])


# ─── EDIÇÃO DO PERFIL DA ONG ──────────────────────────────────────────────────
EMOJI_CHOICES = [
    ('🌟', '🌟 Estrela'),
    ('🌊', '🌊 Onda'),
    ('🌿', '🌿 Planta'),
    ('🐾', '🐾 Pata'),
    ('📚', '📚 Livro'),
    ('🏥', '🏥 Hospital'),
    ('🏠', '🏠 Casa'),
    ('🎵', '🎵 Música'),
    ('🌻', '🌻 Girassol'),
    ('💻', '💻 Tecnologia'),
    ('🍎', '🍎 Alimento'),
    ('♻️', '♻️ Reciclagem'),
    ('👴', '👴 Idosos'),
    ('👶', '👶 Crianças'),
    ('💪', '💪 Empoderamento'),
]


class EditarONGForm(forms.ModelForm):
    emoji = forms.ChoiceField(
        choices=EMOJI_CHOICES,
        label='Ícone da ONG',
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    categorias = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-group'}),
        label='Categorias',
        required=False,
    )

    class Meta:
        model = ONG
        fields = ['nome', 'descricao', 'localizacao', 'emoji', 'foto', 'foto_url', 'categorias', 'urgente']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nome da sua organização',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 4,
                'placeholder': 'Descreva sua missão e como os voluntários podem ajudar...',
                'maxlength': 1000,
            }),
            'localizacao': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: São Paulo, SP',
            }),
            'foto': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'foto_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://exemplo.com/foto.jpg (opcional, usado se não houver upload)',
            }),
            'urgente': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
        labels = {
            'nome': 'Nome da organização',
            'descricao': 'Descrição',
            'localizacao': 'Localização',
            'foto': 'Foto da ONG (upload)',
            'foto_url': 'Ou link de uma foto (se não quiser fazer upload)',
            'urgente': 'Marcar como urgente (precisa de voluntários agora)',
        }

    def clean_nome(self):
        return sanitize(self.cleaned_data['nome'])

    def clean_descricao(self):
        return sanitize(self.cleaned_data['descricao'])

    def clean_localizacao(self):
        return sanitize(self.cleaned_data['localizacao'])

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')
        if foto:
            if foto.size > 3 * 1024 * 1024:
                raise ValidationError('Imagem muito grande. Máximo 3MB.')
            if not foto.content_type.startswith('image/'):
                raise ValidationError('Arquivo inválido. Envie uma imagem.')
            try:
                from PIL import Image
                img = Image.open(foto)
                img.verify()
                foto.seek(0)
            except Exception:
                raise ValidationError('Arquivo corrompido ou não é uma imagem válida.')
        return foto