import pandas as pd
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime


def export_to_excel(queryset, filename, columns=None):
    """Exporta um queryset para Excel"""
    if not queryset.exists():
        return None
    
    # Converte queryset para DataFrame
    df = pd.DataFrame(list(queryset.values()))
    
    # Se columns for especificado, reordena e filtra as colunas
    if columns:
        df = df[[col for col in columns if col in df.columns]]
    
    # Cria resposta HTTP com arquivo Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    # Salva DataFrame como Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    
    return response


def calculate_inss(salario_base):
    """Calcula o desconto do INSS baseado no salário"""
    salario_min = 1320.00
    salario_max = 7507.49
    
    if salario_base <= salario_min:
        return salario_base * 0.075
    elif salario_base <= 2571.29:
        return salario_base * 0.09
    elif salario_base <= 3856.94:
        return salario_base * 0.12
    elif salario_base <= 7507.49:
        return salario_base * 0.14
    else:
        return salario_max * 0.14


def calculate_irrf(salario_base, inss):
    """Calcula o desconto do IRRF baseado no salário"""
    base_calculo = salario_base - inss
    
    if base_calculo <= 1903.98:
        return 0
    elif base_calculo <= 2826.65:
        return base_calculo * 0.075 - 142.80
    elif base_calculo <= 3751.05:
        return base_calculo * 0.15 - 354.80
    elif base_calculo <= 4664.68:
        return base_calculo * 0.225 - 636.13
    else:
        return base_calculo * 0.275 - 869.36


def generate_employee_report(funcionarios):
    """Gera relatório de funcionários"""
    data = []
    for func in funcionarios:
        data.append({
            'Matrícula': func.matricula,
            'Nome': func.nome_completo,
            'CPF': func.cpf,
            'Cargo': func.cargo.nome,
            'Departamento': func.departamento.nome,
            'Salário': func.salario_atual,
            'Data Admissão': func.data_admissao,
            'Status': func.get_status_display(),
            'Idade': func.idade,
            'Tempo Empresa': func.tempo_empresa,
            'E-mail': func.email_corporativo,
            'Telefone': func.telefone,
        })
    
    return pd.DataFrame(data)


def generate_payroll_report(folhas):
    """Gera relatório de folha de pagamento"""
    data = []
    for folha in folhas:
        data.append({
            'Mês/Ano': f"{folha.mes_referencia}/{folha.ano_referencia}",
            'Funcionário': folha.funcionario.nome_completo,
            'Matrícula': folha.funcionario.matricula,
            'Departamento': folha.funcionario.departamento.nome,
            'Salário Base': folha.salario_base,
            'Horas Extras': folha.horas_extras,
            'Valor HE': folha.valor_horas_extras,
            'Adicional Insalubridade': folha.adicional_insalubridade,
            'Adicional Periculosidade': folha.adicional_periculosidade,
            'Outros Proventos': folha.outros_proventos,
            'Total Proventos': folha.calcular_proventos(),
            'INSS': folha.inss,
            'IRRF': folha.irrf,
            'Vale Transporte': folha.vale_transporte,
            'Vale Alimentação': folha.vale_alimentacao,
            'Plano Saúde': folha.plano_saude,
            'Outros Descontos': folha.outros_descontos,
            'Total Descontos': folha.calcular_descontos(),
            'Salário Líquido': folha.salario_liquido,
            'Data Pagamento': folha.data_pagamento,
        })
    
    return pd.DataFrame(data)


from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime


def calcular_salario_por_hora(salario_mensal, turno=None):
    """Calcula o salário por hora baseado no turno"""
    if turno:
        horas_mensais = turno.calcular_horas_mensais()
    else:
        # Padrão 22 dias úteis * 8 horas
        horas_mensais = 22 * 8
    
    return Decimal(salario_mensal) / Decimal(horas_mensais)


def calcular_inss_moz(salario_base):
    """Calcula o INSS conforme legislação de Moçambique"""
    # Tabela INSS Moçambique 2024
    salario = Decimal(salario_base)
    
    # Limites de contribuição (valores aproximados - verificar tabela oficial)
    limite_minimo = Decimal(4390.00)  # Salário mínimo nacional
    limite_maximo = Decimal(21950.00)  # Teto de contribuição
    
    # Taxa de contribuição do trabalhador: 7%
    taxa = Decimal('0.07')
    
    # Base de cálculo é o salário, limitado ao teto
    base_calculo = min(salario, limite_maximo)
    
    # Se o salário for menor que o mínimo, usa o mínimo como base
    if salario < limite_minimo:
        base_calculo = limite_minimo
    
    inss = base_calculo * taxa
    return inss.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_irps_moz(salario_bruto, inss):
    """Calcula o IRPS (Imposto sobre o Rendimento das Pessoas Singulares)"""
    # Base de cálculo: salário bruto - INSS
    base_calculo = Decimal(salario_bruto) - Decimal(inss)
    
    # Tabela progressiva do IRPS Moçambique 2024
    # (verificar tabela oficial atualizada)
    
    if base_calculo <= Decimal(41666.67):  # 1/12 de 500,000 MT
        # Isento
        return Decimal('0.00')
    elif base_calculo <= Decimal(83333.33):  # 1/12 de 1,000,000 MT
        # 10% sobre o excedente
        excedente = base_calculo - Decimal(41666.67)
        irps = excedente * Decimal('0.10')
    elif base_calculo <= Decimal(291666.67):  # 1/12 de 3,500,000 MT
        # 4166.67 + 15% sobre o excedente
        excedente = base_calculo - Decimal(83333.33)
        irps = Decimal('4166.67') + (excedente * Decimal('0.15'))
    elif base_calculo <= Decimal(583333.33):  # 1/12 de 7,000,000 MT
        # 32,500.00 + 20% sobre o excedente
        excedente = base_calculo - Decimal(291666.67)
        irps = Decimal('32500.00') + (excedente * Decimal('0.20'))
    else:
        # 90,833.33 + 25% sobre o excedente
        excedente = base_calculo - Decimal(583333.33)
        irps = Decimal('90833.33') + (excedente * Decimal('0.25'))
    
    return irps.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_salario_liquido_moz(salario_bruto):
    """Calcula o salário líquido com todos os descontos"""
    inss = calcular_inss_moz(salario_bruto)
    irps = calcular_irps_moz(salario_bruto, inss)
    
    return salario_bruto - inss - irps


def calcular_decimo_terceiro(salario_mensal, meses_trabalhados):
    """Calcula o 13º salário proporcional"""
    if meses_trabalhados > 12:
        meses_trabalhados = 12
    
    decimo = (Decimal(salario_mensal) * Decimal(meses_trabalhados)) / Decimal(12)
    return decimo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calcular_ferias_proporcionais(salario_mensal, meses_trabalhados):
    """Calcula férias proporcionais"""
    if meses_trabalhados >= 12:
        # 30 dias de férias + 1/3 constitucional
        valor_ferias = Decimal(salario_mensal) * Decimal(1.33)
    else:
        # Proporcional
        valor_ferias = (Decimal(salario_mensal) * Decimal(meses_trabalhados)) / Decimal(12) * Decimal(1.33)
    
    return valor_ferias.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def verificar_tipo_contrato(salario_mensal):
    """Verifica o tipo de contrato baseado no salário"""
    if salario_mensal <= 15000:
        return 'Estagiário'
    elif salario_mensal <= 25000:
        return 'Júnior'
    elif salario_mensal <= 45000:
        return 'Pleno'
    elif salario_mensal <= 80000:
        return 'Sênior'
    else:
        return 'Gerente/Executivo'