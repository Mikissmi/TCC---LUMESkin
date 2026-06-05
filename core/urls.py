from django.urls import path
from . import views

urlpatterns = [
    # Rota para a tela de cadastro (página inicial do site)
    path('', views.tela_cadastro, name='tela_cadastro'),
    
    # Rota para o questionário
    path('questionario/', views.tela_questionario, name='questionario'),
    
    # Rota para a página de sucesso
    path('sucesso/', views.tela_sucesso, name='sucesso'),
    
    # Rota para o Dashboard (que criamos nos passos anteriores)
    # Certifique-se de que a função 'dashboard_view' exista no seu views.py
    path('dashboard/', views.dashboard_view, name='dashboard'),
]