from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import (
    Empresa,Usuario, Departamento, Cargo, Funcionario, Ferias, Falta,
    FolhaPagamento, AvaliacaoDesempenho, Documento, Treinamento,
    ParticipacaoTreinamento, Advertencia, Beneficio, BeneficioFuncionario,
    TurnoTrabalho, Presenca, JustificativaFalta, ConfiguracaoRH
)
from django.forms import inlineformset_factory
import datetime


class EmpresaRHRegisterForm(UserCreationForm):
    """
    Formulário único para:
    - Criar Empresa
    - Criar Usuário Gestor de RH
    """

    # ===== DADOS DA EMPRESA =====
    nome = forms.CharField(
        label='Nome da Empresa',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    cnpj = forms.CharField(
        label='CNPJ/NUIT',
        max_length=18,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    endereco = forms.CharField(
        label='Endereço',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email_empresa = forms.EmailField(
        label='E-mail da Empresa',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    logo = forms.ImageField(
        label='Logo da Empresa',
        required=False
    )

    # ===== DADOS DO GESTOR RH =====
    username = forms.CharField(
        label='Usuário (login)',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    email = forms.EmailField(
        label='E-mail do Gestor RH',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = (
            'username',
            'email',
            'password1',
            'password2',
        )

    def save(self, commit=True):
        # 🔹 Cria a empresa
        empresa = Empresa.objects.create(
            nome=self.cleaned_data['nome'],
            cnpj=self.cleaned_data['cnpj'],
            endereco=self.cleaned_data['endereco'],
            telefone=self.cleaned_data['telefone'],
            email=self.cleaned_data['email_empresa'],
            logo=self.cleaned_data.get('logo'),
        )

        # 🔹 Cria o usuário Gestor RH
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.empresa = empresa

        if commit:
            user.save()

        return user


class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        exclude = ['empresa', 'criado_em']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do departamento'
            }),
            'sigla': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SIGLA'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do departamento'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }



class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        exclude = ['empresa', 'criado_em']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do cargo'}),
            'nivel_hierarquico': forms.Select(attrs={'class': 'form-select'}),
            'salario_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do cargo'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FuncionarioForm(forms.ModelForm):
    data_nascimento = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    data_admissao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    data_demissao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        required=False
    )

    class Meta:
        model = Funcionario
        exclude = ['empresa', 'usuario', 'criado_em', 'atualizado_em']
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email_corporativo': forms.EmailInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'salario_atual': forms.NumberInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta_corrente': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)  # 👈 AQUI ESTÁ A CORREÇÃO
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields['cargo'].queryset = Cargo.objects.filter(
                empresa=empresa,
                ativo=True
            )
            self.fields['departamento'].queryset = Departamento.objects.filter(
                empresa=empresa,
                ativo=True
            )
            self.fields['turno'].queryset = TurnoTrabalho.objects.filter(
                empresa=empresa,
                ativo=True
            )



class FeriasForm(forms.ModelForm):
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = Ferias
        fields = ['funcionario', 'data_inicio', 'data_fim', 'observacoes']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre as férias'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        
        if data_inicio and data_fim:
            if data_inicio > data_fim:
                raise forms.ValidationError("A data de início deve ser anterior à data de término.")
            
            dias_totais = (data_fim - data_inicio).days + 1
            cleaned_data['dias_totais'] = dias_totais
            # Calcula dias úteis (simplificado)
            dias_uteis = sum(1 for i in range(dias_totais) 
                           if (data_inicio + datetime.timedelta(days=i)).weekday() < 5)
            cleaned_data['dias_uteis'] = dias_uteis
        
        return cleaned_data


class FaltaForm(forms.ModelForm):
    data = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = Falta
        fields = ['funcionario', 'data', 'tipo', 'motivo', 'justificativa', 'horas_abonadas', 'arquivo_comprovante']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Motivo da falta'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Justificativa'}),
            'horas_abonadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '8.0'}),
            'arquivo_comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }


class FolhaPagamentoForm(forms.ModelForm):
    data_pagamento = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = FolhaPagamento
        fields = [
            'funcionario', 'mes_referencia', 'ano_referencia', 'salario_base',
            'horas_extras', 'valor_horas_extras', 'adicional_insalubridade',
            'adicional_periculosidade', 'adicional_tecnico', 'inss', 'irrf',
            'vale_transporte', 'vale_alimentacao', 'plano_saude', 'outros_descontos',
            'outros_proventos', 'data_pagamento'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'mes_referencia': forms.Select(attrs={'class': 'form-select'}),
            'ano_referencia': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'}),
            'salario_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'horas_extras': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '0.0'}),
            'valor_horas_extras': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'adicional_insalubridade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'adicional_periculosidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'adicional_tecnico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'inss': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'irrf': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'vale_transporte': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'vale_alimentacao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'plano_saude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'outros_descontos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'outros_proventos': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }


class AvaliacaoDesempenhoForm(forms.ModelForm):
    periodo_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    periodo_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'funcionario', 'avaliador', 'periodo_inicio', 'periodo_fim',
            'qualidade_trabalho', 'produtividade', 'pontualidade',
            'relacionamento', 'iniciativa', 'lideranca',
            'pontos_fortes', 'pontos_melhoria', 'plano_acao'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'avaliador': forms.Select(attrs={'class': 'form-select'}),
            'qualidade_trabalho': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'produtividade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'pontualidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'relacionamento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'iniciativa': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'lideranca': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'placeholder': '1-5 (opcional)'}),
            'pontos_fortes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Pontos fortes identificados'}),
            'pontos_melhoria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Pontos de melhoria'}),
            'plano_acao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Plano de ação para desenvolvimento'}),
        }


class DocumentoForm(forms.ModelForm):
    data_emissao = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        required=False
    )
    data_validade = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        required=False
    )
    
    class Meta:
        model = Documento
        fields = ['funcionario', 'tipo', 'numero', 'descricao', 'arquivo', 'data_emissao', 'data_validade']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do documento'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class TreinamentoForm(forms.ModelForm):
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = Treinamento
        fields = [
            'nome', 'descricao', 'instrutor', 'carga_horaria',
            'data_inicio', 'data_fim', 'local', 'custo', 'status'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do treinamento'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição detalhada'}),
            'instrutor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do instrutor'}),
            'carga_horaria': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Carga horária em horas'}),
            'local': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Local do treinamento'}),
            'custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ParticipacaoTreinamentoForm(forms.ModelForm):
    class Meta:
        model = ParticipacaoTreinamento
        fields = ['funcionario', 'treinamento', 'status', 'nota', 'observacoes']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'treinamento': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'nota': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 0, 'max': 10, 'placeholder': '0-10'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class AdvertenciaForm(forms.ModelForm):
    data_ocorrencia = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    
    class Meta:
        model = Advertencia
        fields = [
            'funcionario', 'tipo', 'motivo', 'descricao',
            'data_ocorrencia', 'aplicada_por', 'arquivo_documento'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Motivo da advertência'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrição detalhada do ocorrido'}),
            'aplicada_por': forms.Select(attrs={'class': 'form-select'}),
            'arquivo_documento': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BeneficioForm(forms.ModelForm):
    class Meta:
        model = Beneficio
        fields = [
            'nome', 'tipo', 'descricao', 'valor_empresa',
            'valor_funcionario', 'obrigatorio', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do benefício'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descrição do benefício'}),
            'valor_empresa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'valor_funcionario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'obrigatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BeneficioFuncionarioForm(forms.ModelForm):
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        required=False
    )
    
    class Meta:
        model = BeneficioFuncionario
        fields = ['funcionario', 'beneficio', 'data_inicio', 'data_fim', 'ativo']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'beneficio': forms.Select(attrs={'class': 'form-select'}),
        }


# Formulários de Busca
class FuncionarioSearchForm(forms.Form):
    nome = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Buscar por nome...'
    }))
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Todos')] + Funcionario.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FeriasSearchForm(forms.Form):
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Todos')] + Ferias.STATUS_FERIAS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mes = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12, 'placeholder': 'Mês'})
    )
    ano = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ano'})
    )


class FolhaPagamentoSearchForm(forms.Form):
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mes_referencia = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12, 'placeholder': 'Mês'})
    )
    ano_referencia = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ano'})
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class TurnoTrabalhoForm(forms.ModelForm):
    class Meta:
        model = TurnoTrabalho
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Turno da Manhã'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'horas_diarias': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '8.0'}),
            'horas_semanais': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'placeholder': '40.0'}),
            'dias_trabalho_semana': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '5'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do turno'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PresencaForm(forms.ModelForm):
    class Meta:
        model = Presenca
        fields = ['funcionario', 'data', 'hora_entrada', 'hora_saida', 'status', 'observacao']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_entrada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_saida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class MarcacaoPontoForm(forms.Form):
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.filter(status='Ativo'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funcionario'].label = 'Funcionário'


class JustificativaFaltaForm(forms.ModelForm):
    class Meta:
        model = JustificativaFalta
        fields = ['presenca', 'motivo', 'arquivo_comprovante']
        widgets = {
            'presenca': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva o motivo da falta...'}),
            'arquivo_comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ConfiguracaoRHForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoRH
        fields = '__all__'
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'horario_entrada_padrao': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_saida_padrao': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tolerancia_atraso_minutos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10'}),
            'dias_uteis_mes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '22'}),
            'salario_minimo_nacional': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '4390.00'}),
        }


class FolhaPagamentoMozForm(forms.Form):
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.filter(status='Ativo'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    mes_referencia = forms.IntegerField(
        widget=forms.Select(choices=[(i, f'{i}') for i in range(1, 13)], attrs={'class': 'form-select'})
    )
    ano_referencia = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['funcionario'].label = 'Funcionário'
        self.fields['mes_referencia'].label = 'Mês'
        self.fields['ano_referencia'].label = 'Ano'


from django import forms
from .models import TurnoTrabalho

class TurnoTrabalhoForm(forms.ModelForm):
    class Meta:
        model = TurnoTrabalho
        fields = ['nome', 'tipo', 'horas_diarias', 'horas_semanais', 'dias_trabalho_semana', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'horas_diarias': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.25}),
            'horas_semanais': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.25}),
            'dias_trabalho_semana': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
