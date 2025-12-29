from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from datetime import datetime, timedelta, timezone
import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class Empresa(models.Model):
    nome = models.CharField(max_length=200, verbose_name='Nome da Empresa')
    cnpj = models.CharField(max_length=18, unique=True, verbose_name='CNPJ')
    endereco = models.TextField(verbose_name='Endereço')
    telefone = models.CharField(max_length=20, verbose_name='Telefone')
    email = models.EmailField(verbose_name='E-mail')
    logo = models.ImageField(upload_to='empresas/logos/', null=True, blank=True, verbose_name='Logo')
    ativa = models.BooleanField(default=True, verbose_name='Ativa')
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='gestor_rh')

    def __str__(self):
        return f"{self.username} - {self.empresa.nome}"
    
    

class Departamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name='Nome do Departamento')
    sigla = models.CharField(max_length=10, unique=True, verbose_name='Sigla')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        unique_together = ('empresa', 'sigla')
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.sigla})"


class Cargo(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name='Nome do Cargo')
    nivel_hierarquico = models.CharField(max_length=50, choices=[
        ('Auxiliar', 'Auxiliar'),
        ('Tecnico', 'Técnico'),
        ('Especialista', 'Especialista'),
        ('Supervisor', 'Supervisor'),
        ('Chefe', 'Chefe de Departamento'),
        ('Diretor', 'Diretor'),
        ('PCA', 'Administrador Delegado / PCA'),
    ], verbose_name='Nível Hierárquico')
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salário Base')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, verbose_name='Departamento')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.nivel_hierarquico}"


class Funcionario(models.Model):
    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Afastado', 'Afastado'),
        ('Demitido', 'Demitido'),
        ('Aposentado', 'Aposentado'),
    ]
    
    TIPO_CONTRATO = [
        ('Efetivo', 'Efetivo'),
        ('PrazoDeterminado', 'Prazo Determinado'),
        ('Estagiario', 'Estagiário'),
        ('Consultor', 'Consultor'),
    ]
    
    empresa = models.ForeignKey(Empresa,on_delete=models.CASCADE, related_name='funcionarios')
    matricula = models.CharField(max_length=20, unique=True, verbose_name='Matrícula')
    nome_completo = models.CharField(max_length=200, verbose_name='Nome Completo')
    email_corporativo = models.EmailField(unique=True, verbose_name='E-mail Corporativo')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    rg = models.CharField(max_length=20, blank=True, verbose_name='RG')
    data_nascimento = models.DateField(verbose_name='Data de Nascimento')
    telefone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    endereco = models.TextField(verbose_name='Endereço Completo')
    
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, verbose_name='Cargo')
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, verbose_name='Departamento')
    
    data_admissao = models.DateField(verbose_name='Data de Admissão')
    data_demissao = models.DateField(null=True, blank=True, verbose_name='Data de Demissão')
    tipo_contrato = models.CharField(max_length=20, choices=TIPO_CONTRATO, default='CLT', verbose_name='Tipo de Contrato')
    salario_atual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salário Atual')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ativo', verbose_name='Status')
    foto = models.ImageField(upload_to='funcionarios/fotos/', null=True, blank=True, verbose_name='Foto')
    
    # Adicionando campo de turno
    turno = models.ForeignKey('TurnoTrabalho', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Turno de Trabalho')
    
    banco = models.CharField(max_length=100, blank=True, verbose_name='Banco')
    agencia = models.CharField(max_length=20, blank=True, verbose_name='Agência')
    conta_corrente = models.CharField(max_length=20, blank=True, verbose_name='Conta Corrente')
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']
    
    def __str__(self):
        return f"{self.nome_completo} ({self.matricula})"
    
    def get_absolute_url(self):
        return reverse('funcionario_detail', kwargs={'pk': self.pk})
    
    @property
    def idade(self):
        today = datetime.today().date()
        return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
    
    @property
    def tempo_empresa(self):
        today = datetime.today().date()
        end_date = self.data_demissao if self.data_demissao else today
        years = end_date.year - self.data_admissao.year
        months = end_date.month - self.data_admissao.month
        days = end_date.day - self.data_admissao.day
        
        if days < 0:
            months -= 1
            days += 30
        if months < 0:
            years -= 1
            months += 12
        
        return f"{years} anos e {months} meses"
    

class TurnoTrabalho(models.Model):
    TIPO_TURNO = [
        ('8h', '8 horas diárias'),
        ('12h', '12 horas diárias'),
        ('12h_36h', '12h trabalho / 36h folga'),
        ('12h_48h', '12h trabalho / 48h folga'),
        ('6h', '6 horas diárias'),
        ('4h', '4 horas diárias'),
        ('Fim_de_Semana', 'Fins de semana'),
        ('Personalizado', 'Personalizado'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name='Nome do Turno')
    tipo = models.CharField(max_length=20, choices=TIPO_TURNO, verbose_name='Tipo de Turno')
    horas_diarias = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Horas Diárias')
    horas_semanais = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Horas Semanais')
    dias_trabalho_semana = models.IntegerField(default=5, verbose_name='Dias de Trabalho por Semana')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Turno de Trabalho'
        verbose_name_plural = 'Turnos de Trabalho'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.get_tipo_display()}"


    
    def calcular_horas_mensais(self):
        # Calcula horas mensais baseado no tipo de turno
        if self.tipo == '8h':
            return self.horas_diarias * 22  # 22 dias úteis padrão
        elif self.tipo == '12h':
            return self.horas_diarias * 22
        elif self.tipo == '12h_36h':
            # 12h trabalho, 36h folga = 5 dias de trabalho a cada 8 dias
            dias_mes = 30
            ciclos = dias_mes / 4  # Ciclo de 4 dias (1 trabalho + 3 folga aprox.)
            return self.horas_diarias * ciclos * 1  # 1 dia de trabalho por ciclo
        elif self.tipo == '12h_48h':
            # 12h trabalho, 48h folga = 2 dias de trabalho a cada 6 dias
            dias_mes = 30
            ciclos = dias_mes / 6
            return self.horas_diarias * ciclos * 2  # 2 dias de trabalho por ciclo
        elif self.tipo == 'Fim_de_Semana':
            return self.horas_diarias * 8  # Aprox. 4 fins de semana por mês
        else:
            return self.horas_diarias * self.dias_trabalho_semana * 4


class Presenca(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='presencas', verbose_name='Funcionário')
    data = models.DateField(verbose_name='Data')
    hora_entrada = models.TimeField(null=True, blank=True, verbose_name='Hora de Entrada')
    hora_saida = models.TimeField(null=True, blank=True, verbose_name='Hora de Saída')
    horas_trabalhadas = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Horas Trabalhadas')
    
    STATUS_PRESENCA = [
        ('Presente', 'Presente'),
        ('Falta', 'Falta'),
        ('Falta_Justificada', 'Falta Justificada'),
        ('Atraso', 'Atraso'),
        ('Saida_Antecipada', 'Saída Antecipada'),
        ('Feriado', 'Feriado'),
        ('Folga', 'Folga'),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_PRESENCA, default='Presente', verbose_name='Status')
    observacao = models.TextField(blank=True, verbose_name='Observação')
    registrada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Registrada por')
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    atualizada_em = models.DateTimeField(auto_now=True, verbose_name='Atualizada em')
    
    class Meta:
        verbose_name = 'Presença'
        verbose_name_plural = 'Presenças'
        ordering = ['-data', 'funcionario__nome_completo']
        unique_together = ['funcionario', 'data']
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.data} ({self.status})"
    
    def calcular_horas_trabalhadas(self):
        if self.hora_entrada and self.hora_saida:
            entrada = datetime.combine(self.data, self.hora_entrada)
            saida = datetime.combine(self.data, self.hora_saida)
            
            # Se a saída for no dia seguinte (turno da noite)
            if saida < entrada:
                saida += timedelta(days=1)
            
            diff = saida - entrada
            horas = diff.total_seconds() / 3600
            return round(horas, 2)
        return 0
    
    def save(self, *args, **kwargs):
        self.horas_trabalhadas = self.calcular_horas_trabalhadas()
        super().save(*args, **kwargs)
    
    @property
    def horas_faltantes(self):
        # Para cálculo de faltas, usamos o turno do funcionário
        if self.funcionario.turno:
            horas_esperadas = self.funcionario.turno.horas_diarias
            return max(0, horas_esperadas - self.horas_trabalhadas)
        return 0


class JustificativaFalta(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    presenca = models.OneToOneField(Presenca, on_delete=models.CASCADE, related_name='justificativa', verbose_name='Presença/Falta')
    motivo = models.TextField(verbose_name='Motivo da Justificativa')
    arquivo_comprovante = models.FileField(upload_to='justificativas/', null=True, blank=True, verbose_name='Comprovante')
    justificada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Justificada por')
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    class Meta:
        verbose_name = 'Justificativa de Falta'
        verbose_name_plural = 'Justificativas de Faltas'
    
    def __str__(self):
        return f"Justificativa - {self.presenca.funcionario.nome_completo} ({self.presenca.data})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Se a justificativa foi criada dentro de 24h, marca a presença como justificada
        if (timezone.now() - self.criada_em).total_seconds() <= 24 * 3600:
            self.presenca.status = 'Falta_Justificada'
            self.presenca.save()


class ConfiguracaoRH(models.Model):
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, verbose_name='Empresa')
    horario_entrada_padrao = models.TimeField(default='08:00', verbose_name='Horário de Entrada Padrão')
    horario_saida_padrao = models.TimeField(default='17:00', verbose_name='Horário de Saída Padrão')
    tolerancia_atraso_minutos = models.IntegerField(default=10, verbose_name='Tolerância de Atraso (minutos)')
    dias_uteis_mes = models.IntegerField(default=22, verbose_name='Dias Úteis por Mês')
    
    # Configurações de cálculo de salário - Moçambique
    salario_minimo_nacional = models.DecimalField(max_digits=10, decimal_places=2, default=4390.00, verbose_name='Salário Mínimo Nacional (MZN)')
    
    class Meta:
        verbose_name = 'Configuração RH'
        verbose_name_plural = 'Configurações RH'
    
    def __str__(self):
        return f"Configuração - {self.empresa.nome}"


class Ferias(models.Model):
    STATUS_FERIAS = [
        ('Solicitada', 'Solicitada'),
        ('Aprovada', 'Aprovada'),
        ('Rejeitada', 'Rejeitada'),
        ('Cancelada', 'Cancelada'),
        ('Gozada', 'Gozada'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='ferias', verbose_name='Funcionário')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    dias_totais = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Dias Totais')
    dias_uteis = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Dias Úteis')
    status = models.CharField(max_length=20, choices=STATUS_FERIAS, default='Solicitada', verbose_name='Status')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    solicitada_em = models.DateTimeField(auto_now_add=True, verbose_name='Solicitada em')
    aprovada_em = models.DateTimeField(null=True, blank=True, verbose_name='Aprovada em')
    aprovada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='ferias_aprovadas', verbose_name='Aprovada por')
    
    class Meta:
        verbose_name = 'Férias'
        verbose_name_plural = 'Férias'
        ordering = ['-solicitada_em']
    
    def __str__(self):
        return f"Férias {self.funcionario.nome_completo} - {self.data_inicio} a {self.data_fim}"


class Falta(models.Model):
    TIPO_FALTA = [
        ('Justificada', 'Justificada'),
        ('Injustificada', 'Injustificada'),
        ('Atestado', 'Atestado Médico'),
        ('Licenca', 'Licença'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='faltas', verbose_name='Funcionário')
    data = models.DateField(verbose_name='Data da Falta')
    tipo = models.CharField(max_length=20, choices=TIPO_FALTA, verbose_name='Tipo de Falta')
    motivo = models.TextField(blank=True, verbose_name='Motivo/Observação')
    justificativa = models.TextField(blank=True, verbose_name='Justificativa')
    horas_abonadas = models.DecimalField(max_digits=5, decimal_places=2, default=8.0, verbose_name='Horas Abonadas')
    arquivo_comprovante = models.FileField(upload_to='faltas/comprovantes/', null=True, blank=True, verbose_name='Comprovante')
    registrada_em = models.DateTimeField(auto_now_add=True, verbose_name='Registrada em')
    registrada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Registrada por')
    
    class Meta:
        verbose_name = 'Falta'
        verbose_name_plural = 'Faltas'
        ordering = ['-data']
    
    def __str__(self):
        return f"Falta {self.funcionario.nome_completo} - {self.data}"


class FolhaPagamento(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='folhas_pagamento', verbose_name='Funcionário')
    mes_referencia = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name='Mês Referência')
    ano_referencia = models.IntegerField(verbose_name='Ano Referência')
    
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salário Base')
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Horas Extras')
    valor_horas_extras = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Horas Extras')
    
    adicional_insalubridade = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Adicional Insalubridade')
    adicional_periculosidade = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Adicional Periculosidade')
    adicional_tecnico = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Adicional Técnico')
    
    inss = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='INSS')
    irrf = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='IRRF')
    vale_transporte = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Vale Transporte')
    vale_alimentacao = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Vale Alimentação')
    plano_saude = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Plano de Saúde')
    
    outros_descontos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Outros Descontos')
    outros_proventos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Outros Proventos')
    
    salario_liquido = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salário Líquido')
    
    data_pagamento = models.DateField(verbose_name='Data de Pagamento')
    processada_em = models.DateTimeField(auto_now_add=True, verbose_name='Processada em')
    processada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Processada por')
    
    class Meta:
        verbose_name = 'Folha de Pagamento'
        verbose_name_plural = 'Folhas de Pagamento'
        ordering = ['-ano_referencia', '-mes_referencia']
        unique_together = ['funcionario', 'mes_referencia', 'ano_referencia']
    
    def __str__(self):
        return f"Folha {self.funcionario.nome_completo} - {self.mes_referencia}/{self.ano_referencia}"
    
    def calcular_proventos(self):
        return (self.salario_base + self.valor_horas_extras + self.adicional_insalubridade + 
                self.adicional_periculosidade + self.adicional_tecnico + self.outros_proventos)
    
    def calcular_descontos(self):
        return (self.inss + self.irrf + self.vale_transporte + self.vale_alimentacao + 
                self.plano_saude + self.outros_descontos)


class AvaliacaoDesempenho(models.Model):
    STATUS_AVALIACAO = [
        ('Pendente', 'Pendente'),
        ('Em_Andamento', 'Em Andamento'),
        ('Finalizada', 'Finalizada'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='avaliacoes', verbose_name='Funcionário Avaliado')
    avaliador = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='avaliacoes_feitas', verbose_name='Avaliador')
    
    periodo_inicio = models.DateField(verbose_name='Início do Período')
    periodo_fim = models.DateField(verbose_name='Fim do Período')
    
    status = models.CharField(max_length=20, choices=STATUS_AVALIACAO, default='Pendente', verbose_name='Status')
    
    # Critérios de avaliação (1-5)
    qualidade_trabalho = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                             verbose_name='Qualidade do Trabalho')
    produtividade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                        verbose_name='Produtividade')
    pontualidade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                       verbose_name='Pontualidade')
    relacionamento = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                         verbose_name='Relacionamento Interpessoal')
    iniciativa = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                     verbose_name='Iniciativa')
    lideranca = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                    null=True, blank=True, verbose_name='Liderança')
    
    nota_final = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Nota Final')
    
    pontos_fortes = models.TextField(blank=True, verbose_name='Pontos Fortes')
    pontos_melhoria = models.TextField(blank=True, verbose_name='Pontos de Melhoria')
    plano_acao = models.TextField(blank=True, verbose_name='Plano de Ação')
    
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    finalizada_em = models.DateTimeField(null=True, blank=True, verbose_name='Finalizada em')
    
    class Meta:
        verbose_name = 'Avaliação de Desempenho'
        verbose_name_plural = 'Avaliações de Desempenho'
        ordering = ['-criada_em']
    
    def __str__(self):
        return f"Avaliação {self.funcionario.nome_completo} - {self.periodo_inicio} a {self.periodo_fim}"
    
    def calcular_nota_final(self):
        criterios = [self.qualidade_trabalho, self.produtividade, self.pontualidade, 
                     self.relacionamento, self.iniciativa]
        if self.lideranca:
            criterios.append(self.lideranca)
        return sum(criterios) / len(criterios)
    
    def save(self, *args, **kwargs):
        self.nota_final = self.calcular_nota_final()
        super().save(*args, **kwargs)


class Documento(models.Model):
    TIPO_DOCUMENTO = [
        ('BI', 'BI'),
        ('NUIT', 'NUIT'),
        ('Carta_conducao', 'Carta de Condução'),
        ('Cartao_Eleitor', 'Cartão de Eleitor'),
        ('Diploma', 'Diploma'),
        ('Certificado', 'Certificado'),
        ('Contrato', 'Contrato de Trabalho'),
        ('Atestado', 'Atestado Médico'),
        ('Outro', 'Outro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='documentos', verbose_name='Funcionário')
    tipo = models.CharField(max_length=30, choices=TIPO_DOCUMENTO, verbose_name='Tipo de Documento')
    numero = models.CharField(max_length=50, blank=True, verbose_name='Número')
    descricao = models.CharField(max_length=200, blank=True, verbose_name='Descrição')
    arquivo = models.FileField(upload_to='documentos/', verbose_name='Arquivo')
    data_emissao = models.DateField(null=True, blank=True, verbose_name='Data de Emissão')
    data_validade = models.DateField(null=True, blank=True, verbose_name='Data de Validade')
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.funcionario.nome_completo}"


class Treinamento(models.Model):
    STATUS_TREINAMENTO = [
        ('Planejado', 'Planejado'),
        ('Em_Andamento', 'Em Andamento'),
        ('Concluido', 'Concluído'),
        ('Cancelado', 'Cancelado'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200, verbose_name='Nome do Treinamento')
    descricao = models.TextField(verbose_name='Descrição')
    instrutor = models.CharField(max_length=200, verbose_name='Instrutor')
    carga_horaria = models.IntegerField(verbose_name='Carga Horária (horas)')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(verbose_name='Data de Término')
    local = models.CharField(max_length=200, verbose_name='Local')
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Custo')
    status = models.CharField(max_length=20, choices=STATUS_TREINAMENTO, default='Planejado', verbose_name='Status')
    
    participantes = models.ManyToManyField(Funcionario, through='ParticipacaoTreinamento', 
                                           related_name='treinamentos', verbose_name='Participantes')
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = 'Treinamento'
        verbose_name_plural = 'Treinamentos'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return self.nome


class ParticipacaoTreinamento(models.Model):
    STATUS_PARTICIPACAO = [
        ('Inscrito', 'Inscrito'),
        ('Presente', 'Presente'),
        ('Ausente', 'Ausente'),
        ('Concluido', 'Concluído'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name='Funcionário')
    treinamento = models.ForeignKey(Treinamento, on_delete=models.CASCADE, verbose_name='Treinamento')
    status = models.CharField(max_length=20, choices=STATUS_PARTICIPACAO, default='Inscrito', verbose_name='Status')
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name='Nota')
    observacoes = models.TextField(blank=True, verbose_name='Observações')
    
    class Meta:
        verbose_name = 'Participação em Treinamento'
        verbose_name_plural = 'Participações em Treinamentos'
        unique_together = ['funcionario', 'treinamento']
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.treinamento.nome}"


class Advertencia(models.Model):
    TIPO_ADVERTENCIA = [
        ('Advertencia_Verbal', 'Advertência Verbal'),
        ('Advertencia_Escrita', 'Advertência Escrita'),
        ('Suspensao', 'Suspensão'),
        ('Demissao_Por_Justa_Causa', 'Demissão por Justa Causa'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='advertencias', verbose_name='Funcionário')
    tipo = models.CharField(max_length=30, choices=TIPO_ADVERTENCIA, verbose_name='Tipo de Advertência')
    motivo = models.TextField(verbose_name='Motivo')
    descricao = models.TextField(verbose_name='Descrição do Ocorrido')
    data_ocorrencia = models.DateField(verbose_name='Data da Ocorrência')
    
    aplicada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='advertencias_aplicadas'
    )

    
    arquivo_documento = models.FileField(upload_to='advertencias/', null=True, blank=True, verbose_name='Documento Oficial')
    
    criada_em = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    
    class Meta:
        verbose_name = 'Advertência'
        verbose_name_plural = 'Advertências'
        ordering = ['-criada_em']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.funcionario.nome_completo}"


class Beneficio(models.Model):
    TIPO_BENEFICIO = [
        ('Plano_Saude', 'Plano de Saúde'),
        ('Vale_Transporte', 'Vale Transporte'),
        ('Vale_Alimentacao', 'Vale Alimentação'),
        ('Vale_Refeicao', 'Vale Refeição'),
        ('Auxilio_Creche', 'Auxílio Creche'),
        ('Auxilio_Educacao', 'Auxílio Educação'),
        ('Seguro_Vida', 'Seguro de Vida'),
        ('Outro', 'Outro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name='Nome do Benefício')
    tipo = models.CharField(max_length=30, choices=TIPO_BENEFICIO, verbose_name='Tipo')
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    valor_empresa = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Pago pela Empresa')
    valor_funcionario = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Descontado do Funcionário')
    obrigatorio = models.BooleanField(default=False, verbose_name='Obrigatório')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    funcionarios = models.ManyToManyField(Funcionario, through='BeneficioFuncionario', 
                                          related_name='beneficios', verbose_name='Funcionários')
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        verbose_name = 'Benefício'
        verbose_name_plural = 'Benefícios'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class BeneficioFuncionario(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name='Funcionário')
    beneficio = models.ForeignKey(Beneficio, on_delete=models.CASCADE, verbose_name='Benefício')
    data_inicio = models.DateField(verbose_name='Data de Início')
    data_fim = models.DateField(null=True, blank=True, verbose_name='Data de Término')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Benefício do Funcionário'
        verbose_name_plural = 'Benefícios dos Funcionários'
   