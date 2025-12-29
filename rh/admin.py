from django.contrib import admin
from .models import (
    Empresa, Departamento, Cargo, Funcionario, Ferias, Falta,
    FolhaPagamento, AvaliacaoDesempenho, Documento, Treinamento,
    ParticipacaoTreinamento, Advertencia, Beneficio, BeneficioFuncionario,
    TurnoTrabalho, Presenca, JustificativaFalta, ConfiguracaoRH
)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'telefone', 'ativa', 'criada_em')
    list_filter = ('ativa', 'criada_em')
    search_fields = ('nome', 'cnpj')


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em')
    search_fields = ('nome', 'sigla')


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'nivel_hierarquico', 'salario_base', 'departamento', 'ativo')
    list_filter = ('ativo', 'nivel_hierarquico', 'departamento')
    search_fields = ('nome', 'departamento__nome')


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'matricula', 'cargo', 'departamento', 'status', 'data_admissao')
    list_filter = ('status', 'tipo_contrato', 'departamento', 'data_admissao')
    search_fields = ('nome_completo', 'matricula', 'cpf', 'email_corporativo')
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome_completo', 'foto', 'cpf', 'rg', 'data_nascimento', 'telefone', 'endereco')
        }),
        ('Dados Corporativos', {
            'fields': ('matricula', 'email_corporativo', 'cargo', 'departamento', 'supervisor', 'usuario')
        }),
        ('Contratação', {
            'fields': ('data_admissao', 'data_demissao', 'tipo_contrato', 'status', 'salario_atual')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta_corrente'),
            'classes': ('collapse',)
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        })
    )


@admin.register(Ferias)
class FeriasAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data_inicio', 'data_fim', 'dias_uteis', 'status', 'solicitada_em')
    list_filter = ('status', 'data_inicio', 'solicitada_em')
    search_fields = ('funcionario__nome_completo',)
    readonly_fields = ('solicitada_em', 'aprovada_em')


@admin.register(Falta)
class FaltaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data', 'tipo', 'horas_abonadas', 'registrada_em')
    list_filter = ('tipo', 'data', 'registrada_em')
    search_fields = ('funcionario__nome_completo', 'motivo')


@admin.register(FolhaPagamento)
class FolhaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'mes_referencia', 'ano_referencia', 'salario_liquido', 'data_pagamento')
    list_filter = ('mes_referencia', 'ano_referencia', 'data_pagamento')
    search_fields = ('funcionario__nome_completo',)
    readonly_fields = ('processada_em',)


@admin.register(AvaliacaoDesempenho)
class AvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'avaliador', 'nota_final', 'status', 'criada_em')
    list_filter = ('status', 'criada_em')
    search_fields = ('funcionario__nome_completo', 'avaliador__nome_completo')
    readonly_fields = ('criada_em', 'finalizada_em')


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'numero', 'data_emissao', 'data_validade')
    list_filter = ('tipo', 'data_emissao')
    search_fields = ('funcionario__nome_completo', 'numero')


@admin.register(Treinamento)
class TreinamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'instrutor', 'carga_horaria', 'data_inicio', 'status')
    list_filter = ('status', 'data_inicio')
    search_fields = ('nome', 'instrutor')


@admin.register(ParticipacaoTreinamento)
class ParticipacaoTreinamentoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'treinamento', 'status', 'nota')
    list_filter = ('status',)
    search_fields = ('funcionario__nome_completo', 'treinamento__nome')


@admin.register(Advertencia)
class AdvertenciaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'motivo', 'data_ocorrencia', 'criada_em')
    list_filter = ('tipo', 'data_ocorrencia', 'criada_em')
    search_fields = ('funcionario__nome_completo', 'motivo')


@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'valor_empresa', 'valor_funcionario', 'obrigatorio', 'ativo')
    list_filter = ('tipo', 'obrigatorio', 'ativo')
    search_fields = ('nome',)


@admin.register(BeneficioFuncionario)
class BeneficioFuncionarioAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'beneficio', 'data_inicio', 'data_fim', 'ativo')
    list_filter = ('ativo', 'data_inicio')
    search_fields = ('funcionario__nome_completo', 'beneficio__nome')


@admin.register(TurnoTrabalho)
class TurnoTrabalhoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'horas_diarias', 'horas_semanais', 'ativo')
    list_filter = ('ativo', 'tipo')
    search_fields = ('nome',)


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data', 'hora_entrada', 'hora_saida', 'horas_trabalhadas', 'status')
    list_filter = ('status', 'data', 'funcionario__departamento')
    search_fields = ('funcionario__nome_completo',)
    readonly_fields = ('criada_em', 'atualizada_em')


@admin.register(JustificativaFalta)
class JustificativaFaltaAdmin(admin.ModelAdmin):
    list_display = ('presenca', 'criada_em', 'justificada_por')
    list_filter = ('criada_em',)
    search_fields = ('presenca__funcionario__nome_completo', 'motivo')


@admin.register(ConfiguracaoRH)
class ConfiguracaoRHAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'horario_entrada_padrao', 'horario_saida_padrao', 'salario_minimo_nacional')
    search_fields = ('empresa__nome',)
    search_fields = ('funcionario__nome_completo', 'beneficio__nome')