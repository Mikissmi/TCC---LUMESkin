from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import PerfilDermatologico  # Usando o seu modelo real

def tela_cadastro(request):
    if request.method == "POST":
        # Pega os dados digitados no formulário HTML
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        # Cria o usuário no banco de dados seguro do Django
        novo_usuario = User.objects.create_user(
            username=email, 
            email=email, 
            password=senha, 
            first_name=nome
        )
        novo_usuario.save()
        
        # 🌟 MELHORIA: Loga o usuário automaticamente após o cadastro
        auth_login(request, novo_usuario)
        
        # Após cadastrar e logar, envia o usuário direto para o questionário
        return redirect('questionario')
        
    return render(request, 'core/cadastro.html')


def tela_questionario(request):
    if request.method == "POST":
        # 1. Pega as respostas do formulário
        pontos_sol = int(request.POST.get('reacao_sol', 0))
        tipo_pele = request.POST.get('tipo_pele')
        
        # 2. Lógica para definir o Fototipo baseado na resposta do sol
        if pontos_sol == 0:
            fototipo_calculado = "Tipo I"
        elif pontos_sol == 1:
            fototipo_calculado = "Tipo II"
        elif pontos_sol == 2:
            fototipo_calculado = "Tipo III"
        else:
            fototipo_calculado = "Tipo IV"

        # 🌟 MELHORIA: Salva as informações reais vinculadas ao usuário logado
        if request.user.is_authenticated:
            # Busca um perfil existente ou cria um novo para este usuário
            perfil, created = PerfilDermatologico.objects.get_or_create(user=request.user)
            
            # Atualiza os campos do seu modelo
            perfil.tipo_pele = tipo_pele
            perfil.fototipo = fototipo_calculado
            
            # Valores iniciais padrão para o Dashboard não começar zerado:
            perfil.score = 75  # Pontuação inicial simulada
            perfil.streak_days = 1  # Primeiro dia de uso
            perfil.city = "São Paulo, SP"
            perfil.uv_index = 8.5
            
            perfil.save()

        return redirect('dashboard')  # Redireciona direto para o Dashboard!

    return render(request, 'core/questionario.html')


def tela_sucesso(request):
    return render(request, 'core/sucesso.html')


# 🌟 NOVO: View do Dashboard puxando dados do MySQL
def dashboard_view(request):
    # Se o usuário estiver logado, pegamos o perfil dele
    if request.user.is_authenticated:
        perfil = PerfilDermatologico.objects.filter(user=request.user).first()
    else:
        # Caso não esteja logado (acesso de teste), pega o primeiro cadastrado
        perfil = PerfilDermatologico.objects.first()

    context = {
        'perfil': perfil
    }
    return render(request, 'core/dashboard.html', context)


# 🌟 BÔNUS: View para a Tela de Login (visto que você já tem o design pronto)
def tela_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        # Autentica usando o email como username
        usuario = authenticate(request, username=email, password=senha)
        
        if usuario is not None:
            auth_login(request, usuario)
            return redirect('dashboard')
        else:
            # Caso a senha ou usuário estejam errados
            return render(request, 'core/login.html', {'erro': 'Usuário ou senha incorretos'})
            
    return render(request, 'core/login.html')