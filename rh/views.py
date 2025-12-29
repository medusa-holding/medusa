from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Sum, Avg, Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
from django.views.decorators.http import require_POST

from .models import (
    Empresa, Departamento, Cargo, Funcionario, Ferias, Falta,
    FolhaPagamento, AvaliacaoDesempenho, Documento, Treinamento,
    Advertencia, Beneficio
)
from .forms import (
   EmpresaRHRegisterForm, DepartamentoForm, CargoForm,
    FuncionarioForm, FeriasForm, FaltaForm, FolhaPagamentoForm,
    AvaliacaoDesempenhoForm, DocumentoForm, TreinamentoForm,
    AdvertenciaForm, BeneficioForm,
    FuncionarioSearchForm, FeriasSearchForm, FolhaPagamentoSearchForm
)
from .utils import export_to_excel, generate_employee_report, generate_payroll_report


# Views de Autenticação
def register(request):
    if request.method == 'POST':
        form = EmpresaRHRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Empresa cadastrada com sucesso!')
            return redirect('dashboard')
    else:
        form = EmpresaRHRegisterForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    user = request.user
    logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('login')


# Dashboard
@login_required
def dashboard(request):

    empresa = request.user.empresa

    # Estatísticas gerais
    total_funcionarios = Funcionario.objects.filter(empresa=empresa, status='Ativo').count()
    total_departamentos = Departamento.objects.filter(empresa=empresa, ativo=True).count()
    total_cargos = Cargo.objects.filter(empresa=empresa, ativo=True).count()
    
    # Funcionários por departamento
    funcionarios_por_departamento = Departamento.objects.filter(funcionario__empresa=empresa, ativo=True).annotate(
        total_funcionarios=Count('funcionario', filter=Q(funcionario__status='Ativo'))
    ).order_by('-total_funcionarios')[:5]
    
    # Férias recentes
    ferias_recentes = Ferias.objects.filter(funcionario__empresa=empresa, status__in=['Aprovada', 'Solicitada']).order_by('-solicitada_em')[:5]
    
    # Aniversariantes do mês
    mes_atual = datetime.now().month
    aniversariantes = Funcionario.objects.filter(
        empresa=empresa,
        data_nascimento__month=mes_atual,
        status='Ativo'
    ).order_by('data_nascimento__day')[:10]
    
    # Funcionários recentes (últimos 30 dias)
    trinta_dias_atras = datetime.now() - timedelta(days=30)
    funcionarios_recentes = Funcionario.objects.filter(
        empresa=empresa,
        data_admissao__gte=trinta_dias_atras,
        status='Ativo'
    ).count()
    
    context = {
        'total_funcionarios': total_funcionarios,
        'total_departamentos': total_departamentos,
        'total_cargos': total_cargos,
        'funcionarios_por_departamento': funcionarios_por_departamento,
        'ferias_recentes': ferias_recentes,
        'aniversariantes': aniversariantes,
        'funcionarios_recentes': funcionarios_recentes,
    }
    
    return render(request, 'rh/dashboard.html', context)


# Views de Funcionários
class FuncionarioListView(LoginRequiredMixin, ListView):
    model = Funcionario
    template_name = 'rh/funcionario_list.html'
    context_object_name = 'funcionarios'
    paginate_by = 10
    
    def get_queryset(self):

        empresa = self.request.user.empresa

        queryset = Funcionario.objects.filter(empresa=empresa).select_related('cargo', 'departamento').all()
        
        # Filtros de busca
        nome = self.request.GET.get('nome')
        departamento_id = self.request.GET.get('departamento')
        cargo_id = self.request.GET.get('cargo')
        status = self.request.GET.get('status')
        
        if nome:
            queryset = queryset.filter(nome_completo__icontains=nome)
        if departamento_id:
            queryset = queryset.filter(departamento_id=departamento_id)
        if cargo_id:
            queryset = queryset.filter(cargo_id=cargo_id)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('nome_completo')
    
    def get_context_data(self, **kwargs):
        empresa = self.request.user.empresa
        context = super().get_context_data(**kwargs)
        context['search_form'] = FuncionarioSearchForm(self.request.GET)
        context['departamentos'] = Departamento.objects.filter(empresa=empresa, ativo=True)
        context['cargos'] = Cargo.objects.filter(empresa=empresa, ativo=True)
        return context


class FuncionarioDetailView(LoginRequiredMixin, DetailView):
    model = Funcionario
    template_name = 'rh/funcionario_detail.html'
    context_object_name = 'funcionario'

    def get_queryset(self):
        return Funcionario.objects.filter(
            empresa=self.request.user.empresa
        )

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionario = self.get_object()
        context['ferias'] = funcionario.ferias.all()[:5]
        context['faltas'] = funcionario.faltas.all()[:5]
        context['folhas_pagamento'] = funcionario.folhas_pagamento.all()[:5]
        context['avaliacoes'] = funcionario.avaliacoes.all()[:5]
        context['documentos'] = funcionario.documentos.all()[:5]
        return context


class FuncionarioCreateView(LoginRequiredMixin, CreateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'rh/funcionario_form.html'
    success_url = reverse_lazy('funcionario_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Funcionário cadastrado com sucesso!')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.request.user.empresa
        return kwargs



class FuncionarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'rh/funcionario_form.html'
    success_url = reverse_lazy('funcionario_list')
    
    def get_queryset(self):
        return Funcionario.objects.filter(
            empresa=self.request.user.empresa
        )

    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Funcionário atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.request.user.empresa
        return kwargs



class FuncionarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Funcionario
    template_name = 'rh/funcionario_confirm_delete.html'
    success_url = reverse_lazy('funcionario_list')

    def get_queryset(self):
        return Funcionario.objects.filter(
            empresa=self.request.user.empresa
        )
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Funcionário removido com sucesso!')
        return super().delete(request, *args, **kwargs)


# Views de Departamentos
class DepartamentoListView(LoginRequiredMixin, ListView):
    model = Departamento
    template_name = 'rh/departamento_list.html'
    context_object_name = 'departamentos'
    paginate_by = 10
    
    def get_queryset(self):
        return Departamento.objects.filter(
            empresa=self.request.user.empresa
        )

class DepartamentoCreateView(LoginRequiredMixin, CreateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'rh/departamento_form.html'
    success_url = reverse_lazy('departamento_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Departamento criado com sucesso!')
        return super().form_valid(form)


class DepartamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'rh/departamento_form.html'
    success_url = reverse_lazy('departamento_list')

    def get_queryset(self):
        return Departamento.objects.filter(
            empresa=self.request.user.empresa
        )
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Departamento atualizado com sucesso!')
        return super().form_valid(form)


# Views de Cargos
class CargoListView(LoginRequiredMixin, ListView):
    model = Cargo
    template_name = 'rh/cargo_list.html'
    context_object_name = 'cargos'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Cargo.objects.filter(empresa=empresa).select_related('departamento').filter(ativo=True).order_by('nome')


class CargoCreateView(LoginRequiredMixin, CreateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'rh/cargo_form.html'
    success_url = reverse_lazy('cargo_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Cargo criado com sucesso!')
        return super().form_valid(form)


class CargoUpdateView(LoginRequiredMixin, UpdateView):
    model = Cargo
    form_class = CargoForm
    template_name = 'rh/cargo_form.html'
    success_url = reverse_lazy('cargo_list')

    def get_queryset(self):
        return Cargo.objects.filter(
            empresa=self.request.user.empresa
        )
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Cargo atualizado com sucesso!')
        return super().form_valid(form)
    
from django.http import JsonResponse

@login_required
def obter_salario_cargo(request):
    cargo_id = request.GET.get('cargo_id')

    try:
        cargo = Cargo.objects.get(
            id=cargo_id,
            empresa=request.user.empresa
        )
        return JsonResponse({'salario': float(cargo.salario_base)})
    except Cargo.DoesNotExist:
        return JsonResponse({'salario': 0})



# Views de Férias
@login_required
def ferias_list(request):
    empresa = request.user.empresa
    ferias = Ferias.objects.filter(funcionario__empresa=empresa).select_related('funcionario').all().order_by('-solicitada_em')
    
    # Filtros
    funcionario_id = request.GET.get('funcionario')
    status = request.GET.get('status')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    if funcionario_id:
        ferias = ferias.filter(funcionario_id=funcionario_id)
    if status:
        ferias = ferias.filter(status=status)
    if mes:
        ferias = ferias.filter(data_inicio__month=mes)
    if ano:
        ferias = ferias.filter(data_inicio__year=ano)
    
    paginator = Paginator(ferias, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': FeriasSearchForm(request.GET),
    }
    return render(request, 'rh/ferias_list.html', context)


@login_required
def ferias_create(request):
    if request.method == 'POST':
        form = FeriasForm(request.POST)
        if form.is_valid():
            ferias = form.save(commit=False)
            ferias.empresa = request.user.empresa
            ferias.funcionario = get_object_or_404(
                Funcionario,
                id=ferias.funcionario.id,
            )
            # Calcular dias automaticamente
            dias_totais = (ferias.data_fim - ferias.data_inicio).days + 1
            dias_uteis = sum(1 for i in range(dias_totais) 
                           if (ferias.data_inicio + timedelta(days=i)).weekday() < 5)
            ferias.dias_totais = dias_totais
            ferias.dias_uteis = dias_uteis
            ferias.save()
            messages.success(request, 'Solicitação de férias criada com sucesso!')
            return redirect('ferias_list')
    else:
        form = FeriasForm()
    
    return render(request, 'rh/ferias_form.html', {'form': form})


@login_required
def ferias_aprovar(request, pk):
    ferias = get_object_or_404(Ferias, pk=pk, funcionario__empresa=request.user.empresa)
    if request.method == 'POST':
        ferias.status = 'Aprovada'
        ferias.aprovada_em = datetime.now()
        ferias.aprovada_por = request.user
        ferias.save()
        messages.success(request, f'Férias de {ferias.funcionario.nome_completo} aprovadas!')
    return redirect('ferias_list')


@login_required
def ferias_rejeitar(request, pk):
    ferias = get_object_or_404(Ferias, pk=pk, funcionario__empresa=request.user.empresa)
    if request.method == 'POST':
        ferias.status = 'Rejeitada'
        ferias.save()
        messages.warning(request, f'Férias de {ferias.funcionario.nome_completo} rejeitadas.')
    return redirect('ferias_list')


# Views de Faltas
class FaltaListView(LoginRequiredMixin, ListView):
    model = Falta
    template_name = 'rh/falta_list.html'
    context_object_name = 'faltas'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Falta.objects.filter(funcionario__empresa=empresa).select_related('funcionario').all().order_by('-data')


class FaltaCreateView(LoginRequiredMixin, CreateView):
    model = Falta
    form_class = FaltaForm
    template_name = 'rh/falta_form.html'
    success_url = reverse_lazy('falta_list')
    
    def form_valid(self, form):
        falta = form.save(commit=False)
        falta.empresa = self.request.user.empresa
        falta.registrada_por = self.request.user
        falta.save()
        messages.success(self.request, 'Falta registrada com sucesso!')
        return redirect(self.success_url)



# Views de Folha de Pagamento
@login_required
def folha_pagamento_list(request):
    empresa = request.user.empresa
    folhas = FolhaPagamento.objects.filter(empresa=empresa).select_related('funcionario__cargo', 'funcionario__departamento').all().order_by('-ano_referencia', '-mes_referencia')
    
    # Filtros
    funcionario_id = request.GET.get('funcionario')
    mes = request.GET.get('mes_referencia')
    ano = request.GET.get('ano_referencia')
    departamento_id = request.GET.get('departamento')
    
    if funcionario_id:
        folhas = folhas.filter(funcionario_id=funcionario_id)
    if mes:
        folhas = folhas.filter(mes_referencia=mes)
    if ano:
        folhas = folhas.filter(ano_referencia=ano)
    if departamento_id:
        folhas = folhas.filter(funcionario__departamento_id=departamento_id)
    
    # Exportação Excel
    if request.GET.get('export') == 'excel':
        df = generate_payroll_report(folhas)
        return export_to_excel(folhas, 'folha_pagamento', [
            'funcionario__nome_completo', 'mes_referencia', 'ano_referencia',
            'salario_base', 'salario_liquido', 'data_pagamento'
        ])
    
    paginator = Paginator(folhas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': FolhaPagamentoSearchForm(request.GET),
    }
    return render(request, 'rh/folha_pagamento_list.html', context)


@login_required
def folha_pagamento_create(request):
    if request.method == 'POST':
        form = FolhaPagamentoForm(request.POST)
        if form.is_valid():
            folha = form.save(commit=False)
            folha.funcionario = get_object_or_404(
                Funcionario,
                id=folha.funcionario.id,
                empresa=request.user.empresa
            )
            folha.processada_por = request.user
            # Calcular salário líquido
            proventos = folha.calcular_proventos()
            descontos = folha.calcular_descontos()
            folha.salario_liquido = proventos - descontos
            folha.save()
            messages.success(request, 'Folha de pagamento processada com sucesso!')
            return redirect('folha_pagamento_list')
    else:
        form = FolhaPagamentoForm()
    
    return render(request, 'rh/folha_pagamento_form.html', {'form': form})


# Views de Avaliação de Desempenho
class AvaliacaoListView(LoginRequiredMixin, ListView):
    model = AvaliacaoDesempenho
    template_name = 'rh/avaliacao_list.html'
    context_object_name = 'avaliacoes'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return AvaliacaoDesempenho.objects.filter(empresa=empresa).select_related('funcionario', 'avaliador').all().order_by('-criada_em')


class AvaliacaoCreateView(LoginRequiredMixin, CreateView):
    model = AvaliacaoDesempenho
    form_class = AvaliacaoDesempenhoForm
    template_name = 'rh/avaliacao_form.html'
    success_url = reverse_lazy('avaliacao_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        avaliacao = form.save(commit=False)
        avaliacao.nota_final = avaliacao.calcular_nota_final()
        if avaliacao.status == 'Finalizada':
            from django.utils import timezone
            avaliacao.finalizada_em = timezone.now()
        avaliacao.save()
        messages.success(self.request, 'Avaliação de desempenho criada com sucesso!')
        return super().form_valid(form)


# Views de Documentos
class DocumentoListView(LoginRequiredMixin, ListView):
    model = Documento
    template_name = 'rh/documento_list.html'
    context_object_name = 'documentos'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Documento.objects.filter(empresa=empresa).select_related('funcionario').all().order_by('-criado_em')


class DocumentoCreateView(LoginRequiredMixin, CreateView):
    model = Documento
    form_class = DocumentoForm
    template_name = 'rh/documento_form.html'
    success_url = reverse_lazy('documento_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Documento cadastrado com sucesso!')
        return super().form_valid(form)


# Views de Treinamentos
class TreinamentoListView(LoginRequiredMixin, ListView):
    model = Treinamento
    template_name = 'rh/treinamento_list.html'
    context_object_name = 'treinamentos'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Treinamento.objects.filter(empresa=empresa).order_by('-data_inicio')


class TreinamentoCreateView(LoginRequiredMixin, CreateView):
    model = Treinamento
    form_class = TreinamentoForm
    template_name = 'rh/treinamento_form.html'
    success_url = reverse_lazy('treinamento_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Treinamento criado com sucesso!')
        return super().form_valid(form)


# Views de Advertências
class AdvertenciaListView(LoginRequiredMixin, ListView):
    model = Advertencia
    template_name = 'rh/advertencia_list.html'
    context_object_name = 'advertencias'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Advertencia.objects.filter(empresa=empresa).select_related('funcionario', 'aplicada_por').all().order_by('-criada_em')


class AdvertenciaCreateView(LoginRequiredMixin, CreateView):
    model = Advertencia
    form_class = AdvertenciaForm
    template_name = 'rh/advertencia_form.html'
    success_url = reverse_lazy('advertencia_list')
    
    def form_valid(self, form):
        advertencia = form.save(commit=False)
        advertencia.empresa = self.request.user.empresa
        advertencia.aplicada_por = self.request.user
        advertencia.save()
        messages.success(self.request, 'Advertência registrada com sucesso!')
        return redirect(self.success_url)


# Views de Benefícios
class BeneficioListView(LoginRequiredMixin, ListView):
    model = Beneficio
    template_name = 'rh/beneficio_list.html'
    context_object_name = 'beneficios'
    paginate_by = 10
    
    def get_queryset(self):
        empresa = self.request.user.empresa
        return Beneficio.objects.filter(empresa=empresa, ativo=True).order_by('nome')


class BeneficioCreateView(LoginRequiredMixin, CreateView):
    model = Beneficio
    form_class = BeneficioForm
    template_name = 'rh/beneficio_form.html'
    success_url = reverse_lazy('beneficio_list')
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Benefício criado com sucesso!')
        return super().form_valid(form)


# Views de Relatórios
@login_required
def relatorios(request):
    empresa = request.user.empresa
    # Estatísticas para os relatórios
    total_funcionarios = Funcionario.objects.filter(empresa=empresa, status='Ativo').count()
    total_folha = FolhaPagamento.objects.filter(
        empresa=empresa,
        mes_referencia=datetime.now().month,
        ano_referencia=datetime.now().year
    ).aggregate(total=Sum('salario_liquido'))['total'] or 0
    
    # Top 5 departamentos por quantidade de funcionários
    top_departamentos = Departamento.objects.filter(empresa=empresa, ativo=True).annotate(
        total=Count('funcionario', filter=Q(funcionario__status='Ativo'))
    ).order_by('-total')[:5]
    
    # Média de salários por departamento
    media_salarial = (
        total_folha / total_funcionarios
        if total_funcionarios > 0
        else 0
    )
    context = {
        'total_funcionarios': total_funcionarios,
        'total_folha': total_folha,
        'top_departamentos': top_departamentos,
        'media_salarial': media_salarial,
    }
    
    return render(request, 'rh/relatorios.html', context)


# API para gráficos do dashboard
@login_required
def dashboard_data(request):
    empresa = request.user.empresa
    # Dados para gráficos
    
    # Funcionários por departamento
    dept_data = list(Departamento.objects.filter(empresa=empresa, ativo=True).annotate(
        total=Count('funcionario', filter=Q(funcionario__status='Ativo'))
    ).values('nome', 'total'))
    
    # Status dos funcionários
    status_data = list(Funcionario.objects.filter(empresa=empresa).values('status').annotate(
        total=Count('id')
    ))
    
    # Férias por mês (últimos 6 meses)
    meses = []
    ferias_count = []
    for i in range(6):
        data = datetime.now() - timedelta(days=30*i)
        meses.append(data.strftime('%b/%Y'))
        count = Ferias.objects.filter(
            funcionario__empresa=empresa,
            data_inicio__month=data.month,
            data_inicio__year=data.year
        ).count()
        ferias_count.append(count)
    
    data = {
        'departamentos': dept_data,
        'status_funcionarios': status_data,
        'ferias_mensal': {
            'labels': meses[::-1],
            'data': ferias_count[::-1]
        }
    }
    
    return JsonResponse(data)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import Funcionario, TurnoTrabalho, Presenca, JustificativaFalta, ConfiguracaoRH
from .forms import MarcacaoPontoForm, JustificativaFaltaForm, FolhaPagamentoMozForm
from .utils import calcular_inss_moz, calcular_irps_moz, calcular_salario_por_hora


@login_required
def marcar_presenca(request):
    empresa = request.user.empresa
    agora = timezone.now()
    data_atual = agora.date()

    funcionarios = Funcionario.objects.filter(empresa=empresa, status='Ativo').select_related('turno', 'departamento').order_by('nome_completo')
    
    # Buscar presenças do dia
    presencas_hoje = Presenca.objects.filter(empresa=empresa, data=data_atual).select_related('funcionario', 'funcionario__turno')
    
    # Criar dicionário de presenças para fácil acesso
    presencas_dict = {p.funcionario_id: p for p in presencas_hoje}
    
    if request.method == 'POST':
        form = MarcacaoPontoForm(request.POST)
        if form.is_valid():
            funcionario = get_object_or_404(
                Funcionario,
                id=form.cleaned_data['funcionario'].id,
                empresa=empresa
            )

            tipo_marcacao = request.POST.get('tipo_marcacao')
            
            # Buscar ou criar presença do dia
            presenca, created = Presenca.objects.filter(empresa=empresa).get_or_create(
                empresa=empresa,
                funcionario=funcionario,
                data=data_atual,
                defaults={'registrada_por': request.user}
            )
            
            agora = timezone.now().time()
            
            if tipo_marcacao == 'entrada':
                if presenca.hora_entrada:
                    messages.warning(request, f'{funcionario.nome_completo} já marcou entrada às {presenca.hora_entrada}')
                else:
                    presenca.hora_entrada = agora
                    presenca.registrada_por = request.user
                    presenca.save()
                    messages.success(request, f'Entrada de {funcionario.nome_completo} registrada com sucesso!')
            
            elif tipo_marcacao == 'saida':
                if not presenca.hora_entrada:
                    messages.error(request, f'{funcionario.nome_completo} precisa marcar entrada primeiro!')
                elif presenca.hora_saida:
                    messages.warning(request, f'{funcionario.nome_completo} já marcou saída às {presenca.hora_saida}')
                else:
                    presenca.hora_saida = agora
                    presenca.registrada_por = request.user
                    presenca.save()
                    
                    # Calcular horas trabalhadas
                    horas_trabalhadas = presenca.horas_trabalhadas
                    messages.success(request, f'Saída de {funcionario.nome_completo} registrada! Horas trabalhadas: {horas_trabalhadas}h')
            
            return redirect('marcar_presenca')
    else:
        form = MarcacaoPontoForm()
    
    context = {
        'data_atual': data_atual,
        'agora': agora,
        'funcionarios': funcionarios,
        'presencas_dict': presencas_dict,
        'form': form,
    }
    return render(request, 'rh/marcar_presenca.html', context)


@login_required
def faltas_do_dia(request):
    empresa = request.user.empresa
    data_atual = timezone.now().date()
    
    # Buscar funcionários que não marcaram presença hoje
    funcionarios_com_presenca = Presenca.objects.filter(empresa=empresa, data=data_atual).values_list('funcionario_id', flat=True)
    faltas_hoje = Funcionario.objects.filter(empresa=empresa, status='Ativo').exclude(id__in=funcionarios_com_presenca)
    
    # Criar presenças como falta para quem não marcou
    for funcionario in faltas_hoje:
        Presenca.objects.filter(empresa=empresa).get_or_create(
            funcionario=funcionario,
            data=data_atual,
            defaults={'status': 'Falta', 'registrada_por': request.user}
        )
    
    # Buscar todas as faltas do dia
    presencas_falta = Presenca.objects.filter(empresa=empresa, data=data_atual, status__in=['Falta', 'Falta_Justificada']).select_related('funcionario', 'justificativa')
    
    if request.method == 'POST':
        presenca_id = request.POST.get('presenca_id')
        tipo_acao = request.POST.get('tipo_acao')
        
        presenca = get_object_or_404(Presenca, id=presenca_id, empresa=empresa)
        
        if tipo_acao == 'justificar':
            # Verificar se está dentro do prazo de 24h
            if (timezone.now() - presenca.criada_em).total_seconds() <= 24 * 3600:
                motivo = request.POST.get(f'motivo_{presenca_id}')
                if motivo:
                    JustificativaFalta.objects.create(
                        presenca=presenca,
                        motivo=motivo,
                        justificada_por=request.user
                    )
                    messages.success(request, f'Falta de {presenca.funcionario.nome_completo} justificada com sucesso!')
                else:
                    messages.error(request, 'Por favor, informe o motivo da justificativa.')
            else:
                messages.error(request, 'Prazo de 24h para justificativa expirado!')
        
        elif tipo_acao == 'manter_falta':
            presenca.status = 'Falta'
            presenca.save()
            messages.info(request, f'Falta de {presenca.funcionario.nome_completo} mantida.')
        
        return redirect('faltas_do_dia')
    
    context = {
        'data_atual': data_atual,
        'presencas_falta': presencas_falta,
    }
    return render(request, 'rh/faltas_do_dia.html', context)


@login_required
def gerar_folha_moz(request):
    empresa = request.user.empresa
    if request.method == 'POST':
        form = FolhaPagamentoMozForm(request.POST)
        if form.is_valid():
            funcionario = get_object_or_404(
                Funcionario,
                id=form.cleaned_data['funcionario'].id,
                empresa=empresa
            )

            mes = form.cleaned_data['mes_referencia']
            ano = form.cleaned_data['ano_referencia']
            
            # Buscar presenças do mês
            presencas_mes = Presenca.objects.filter(
                empresa=empresa,
                funcionario=funcionario,
                data__month=mes,
                data__year=ano,
                status__in=['Presente', 'Falta_Justificada']
            )
            
            # Calcular horas trabalhadas no mês
            horas_trabalhadas = sum(p.horas_trabalhadas for p in presencas_mes)
            
            # Calcular salário por hora
            salario_hora = calcular_salario_por_hora(funcionario.salario_atual, funcionario.turno)
            
            # Calcular salário bruto baseado nas horas trabalhadas
            salario_bruto = horas_trabalhadas * salario_hora
            
            # Calcular INSS e IRPS (Moçambique)
            inss = calcular_inss_moz(salario_bruto)
            irps = calcular_irps_moz(salario_bruto, inss)
            
            # Outros descontos
            faltas_nao_justificadas = Presenca.objects.filter(
                funcionario=funcionario,
                data__month=mes,
                data__year=ano,
                status='Falta'
            ).count()
            
            # Desconto por faltas (valor da hora * horas diárias * dias de falta)
            desconto_faltas = faltas_nao_justificadas * salario_hora * (funcionario.turno.horas_diarias if funcionario.turno else 8)
            
            salario_liquido = salario_bruto - inss - irps - desconto_faltas
            
            context = {
                'funcionario': funcionario,
                'mes': mes,
                'ano': ano,
                'presencas_mes': presencas_mes,
                'horas_trabalhadas': horas_trabalhadas,
                'salario_hora': salario_hora,
                'salario_bruto': salario_bruto,
                'inss': inss,
                'irps': irps,
                'desconto_faltas': desconto_faltas,
                'salario_liquido': salario_liquido,
                'faltas_nao_justificadas': faltas_nao_justificadas,
            }
            
            return render(request, 'rh/payslip_moz.html', context)
    else:
        form = FolhaPagamentoMozForm()
    
    return render(request, 'rh/gerar_folha_moz.html', {'form': form})


@login_required
def payslip_pdf(request, funcionario_id, mes, ano):
    # Função para gerar PDF do payslip
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    empresa = request.user.empresa
    
    funcionario = get_object_or_404(Funcionario, id=funcionario_id, empresa=empresa)
    
    # Buscar dados da folha
    presencas_mes = Presenca.objects.filter(
        empresa=empresa,
        funcionario=funcionario,
        data__month=mes,
        data__year=ano,
        status__in=['Presente', 'Falta_Justificada']
    )
    
    horas_trabalhadas = sum(p.horas_trabalhadas for p in presencas_mes)
    salario_hora = calcular_salario_por_hora(funcionario.salario_atual, funcionario.turno)
    salario_bruto = horas_trabalhadas * salario_hora
    inss = calcular_inss_moz(salario_bruto)
    irps = calcular_irps_moz(salario_bruto, inss)
    
    faltas_nao_justificadas = Presenca.objects.filter(
        funcionario=funcionario,
        data__month=mes,
        data__year=ano,
        status='Falta'
    ).count()
    
    desconto_faltas = faltas_nao_justificadas * salario_hora * (funcionario.turno.horas_diarias if funcionario.turno else 8)
    salario_liquido = salario_bruto - inss - irps - desconto_faltas
    
    # Criar PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payslip_{funcionario.matricula}_{mes}_{ano}.pdf"'
    
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    
    # Cabeçalho
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "PAYSLIP - RECIBO DE VENCIMENTOS")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 95, f"Funcionário: {funcionario.nome_completo}")
    p.drawString(50, height - 110, f"Matrícula: {funcionario.matricula}")
    p.drawString(50, height - 125, f"Cargo: {funcionario.cargo.nome}")
    p.drawString(50, height - 140, f"Período: {mes}/{ano}")
    
    # Vencimentos
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 180, "VENCIMENTOS")
    
    p.setFont("Helvetica", 10)
    y = height - 200
    p.drawString(50, y, f"Salário Base (Horas): {horas_trabalhadas}h x {salario_hora:.2f}/h")
    p.drawString(400, y, f"{salario_bruto:.2f}")
    
    # Descontos
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "DESCONTOS")
    
    p.setFont("Helvetica", 10)
    y -= 20
    p.drawString(50, y, "INSS")
    p.drawString(400, y, f"{inss:.2f}")
    
    y -= 15
    p.drawString(50, y, "IRPS")
    p.drawString(400, y, f"{irps:.2f}")
    
    if desconto_faltas > 0:
        y -= 15
        p.drawString(50, y, f"Faltas ({faltas_nao_justificadas} dias)")
        p.drawString(400, y, f"{desconto_faltas:.2f}")
    
    # Total
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "TOTAL LÍQUIDO")
    p.drawString(400, y, f"{salario_liquido:.2f}")
    
    p.showPage()
    p.save()
    
    return response


from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import TurnoTrabalho
from .forms import TurnoTrabalhoForm

class TurnoListView(LoginRequiredMixin, ListView):
    model = TurnoTrabalho
    template_name = 'rh/turno_list.html'
    context_object_name = 'turnos'
    
    def get_queryset(self):
        return TurnoTrabalho.objects.filter(empresa=self.request.user.empresa).order_by('nome')


class TurnoCreateView(LoginRequiredMixin, CreateView):
    model = TurnoTrabalho
    form_class = TurnoTrabalhoForm
    template_name = 'rh/turno_form.html'
    success_url = reverse_lazy('turno_list')

    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        messages.success(self.request, 'Turno de trabalho criado com sucesso!')
        return super().form_valid(form)


class TurnoUpdateView(LoginRequiredMixin, UpdateView):
    model = TurnoTrabalho
    form_class = TurnoTrabalhoForm
    template_name = 'rh/turno_form.html'
    success_url = reverse_lazy('turno_list')

    def get_queryset(self):
        return TurnoTrabalho.objects.filter(empresa=self.request.user.empresa)

    def form_valid(self, form):
        messages.success(self.request, 'Turno de trabalho atualizado com sucesso!')
        return super().form_valid(form)


class TurnoDeleteView(LoginRequiredMixin, DeleteView):
    model = TurnoTrabalho
    template_name = 'rh/turno_confirm_delete.html'
    success_url = reverse_lazy('turno_list')

    def get_queryset(self):
        return TurnoTrabalho.objects.filter(empresa=self.request.user.empresa)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Turno de trabalho removido com sucesso!')
        return super().delete(request, *args, **kwargs)
