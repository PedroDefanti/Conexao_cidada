import re
import bleach
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from .models import Usuario, Inscricao


ALLOWED_TAGS = []   # sem HTML nas entradas do usuário


def sanitize(value):
    """Remove qualquer HTML/JS de entrada de texto."""
    return bleach.clean(value, tags=ALLOWED_TAGS, strip=True).strip()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'seu@email.com',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def clean_username(self):
        return sanitize(self.cleaned_data['username'])


class CadastroVoluntarioForm(UserCreationForm):
    nome = forms.CharField(
        label='Nome Completo',
        max_length=150,
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
        user.username = self.cleaned_data['email']   # email como username
        user.tipo = 'voluntario'
        if commit:
            user.save()
        return user


class CadastroONGForm(UserCreationForm):
    nome_organizacao = forms.CharField(
        label='Nome da Organização',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome da instituição'})
    )
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
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
        cnpj = re.sub(r'\D', '', self.cleaned_data['cnpj'])
        if len(cnpj) != 14:
            raise ValidationError('CNPJ inválido. Informe 14 dígitos.')
        # formata
        return f'{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}'

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


class InscricaoForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = ['mensagem', 'disponibilidade']
        widgets = {
            'mensagem': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Por que você quer participar desta causa?',
                'rows': 4,
                'maxlength': 500,
            }),
            'disponibilidade': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: fins de semana, tardes de terça e quinta...',
                'maxlength': 200,
            }),
        }
        labels = {
            'mensagem': 'Mensagem (opcional)',
            'disponibilidade': 'Disponibilidade',
        }

    def clean_mensagem(self):
        return sanitize(self.cleaned_data.get('mensagem', ''))

    def clean_disponibilidade(self):
        return sanitize(self.cleaned_data['disponibilidade'])
