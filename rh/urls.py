from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import logout_view
from .views import TurnoListView, TurnoCreateView, TurnoUpdateView, TurnoDeleteView


urlpatterns = [
    # Autenticação
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard-data/', views.dashboard_data, name='dashboard_data'),
    
    # Funcionários
    path('funcionarios/', views.FuncionarioListView.as_view(), name='funcionario_list'),
    path('funcionarios/novo/', views.FuncionarioCreateView.as_view(), name='funcionario_create'),
    path('funcionarios/<int:pk>/', views.FuncionarioDetailView.as_view(), name='funcionario_detail'),
    path('funcionarios/<int:pk>/editar/', views.FuncionarioUpdateView.as_view(), name='funcionario_update'),
    path('funcionarios/<int:pk>/excluir/', views.FuncionarioDeleteView.as_view(), name='funcionario_delete'),
    
    # Departamentos
    path('departamentos/', views.DepartamentoListView.as_view(), name='departamento_list'),
    path('departamentos/novo/', views.DepartamentoCreateView.as_view(), name='departamento_create'),
    path('departamentos/<int:pk>/editar/', views.DepartamentoUpdateView.as_view(), name='departamento_update'),
    
    # Cargos
    path('cargos/', views.CargoListView.as_view(), name='cargo_list'),
    path('cargos/novo/', views.CargoCreateView.as_view(), name='cargo_create'),
    path('cargos/<int:pk>/editar/', views.CargoUpdateView.as_view(), name='cargo_update'),
    path('ajax/obter-salario-cargo/', views.obter_salario_cargo, name='obter_salario_cargo'),
    
    # Férias
    path('ferias/', views.ferias_list, name='ferias_list'),
    path('ferias/novo/', views.ferias_create, name='ferias_create'),
    path('ferias/<int:pk>/aprovar/', views.ferias_aprovar, name='ferias_aprovar'),
    path('ferias/<int:pk>/rejeitar/', views.ferias_rejeitar, name='ferias_rejeitar'),
    
    # Faltas
    path('faltas/', views.FaltaListView.as_view(), name='falta_list'),
    path('faltas/novo/', views.FaltaCreateView.as_view(), name='falta_create'),
    
    # Folha de Pagamento
    path('folha-pagamento/', views.folha_pagamento_list, name='folha_pagamento_list'),
    path('folha-pagamento/novo/', views.folha_pagamento_create, name='folha_pagamento_create'),
    
    # Avaliações de Desempenho
    path('avaliacoes/', views.AvaliacaoListView.as_view(), name='avaliacao_list'),
    path('avaliacoes/novo/', views.AvaliacaoCreateView.as_view(), name='avaliacao_create'),
    
    # Documentos
    path('documentos/', views.DocumentoListView.as_view(), name='documento_list'),
    path('documentos/novo/', views.DocumentoCreateView.as_view(), name='documento_create'),
    
    # Treinamentos
    path('treinamentos/', views.TreinamentoListView.as_view(), name='treinamento_list'),
    path('treinamentos/novo/', views.TreinamentoCreateView.as_view(), name='treinamento_create'),
    
    # Advertências
    path('advertencias/', views.AdvertenciaListView.as_view(), name='advertencia_list'),
    path('advertencias/novo/', views.AdvertenciaCreateView.as_view(), name='advertencia_create'),
    
    # Benefícios
    path('beneficios/', views.BeneficioListView.as_view(), name='beneficio_list'),
    path('beneficios/novo/', views.BeneficioCreateView.as_view(), name='beneficio_create'),
    
    # Presença e Ponto
    path('presenca/', views.marcar_presenca, name='marcar_presenca'),
    path('faltas/dia/', views.faltas_do_dia, name='faltas_do_dia'),
    path('folha/moz/', views.gerar_folha_moz, name='gerar_folha_moz'),
    path('payslip/<int:funcionario_id>/<int:mes>/<int:ano>/', views.payslip_pdf, name='payslip_pdf'),

    # Turnos
    path('turnos/', TurnoListView.as_view(), name='turno_list'),
    path('turnos/novo/', TurnoCreateView.as_view(), name='turno_create'),
    path('turnos/<int:pk>/editar/', TurnoUpdateView.as_view(), name='turno_update'),
    path('turnos/<int:pk>/deletar/', TurnoDeleteView.as_view(), name='turno_delete'),
    
    # Relatórios
    path('relatorios/', views.relatorios, name='relatorios'),


]