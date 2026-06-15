from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import PerfilDermatologico 

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
        
        #Loga o usuário automaticamente após o cadastro
        auth_login(request, novo_usuario)
        
        # Após cadastrar e logar, envia o usuário direto para o questionário
        return redirect('questionario')
        
    return render(request, 'core/cadastro.html')


from django.shortcuts import render, redirect
from .models import PerfilDermatologico  # Garanta que o import está correto

def tela_questionario(request):
    if request.method == "POST":
        # 1. Pega TODAS as respostas do formulário HTML usando o atributo 'name'
        idade = request.POST.get('idade')
        tipo_pele = request.POST.get('tipo_pele')
        alergias = request.POST.get('alergias')
        descricao_alergia = request.POST.get('descricaoalergia')
        maquiagem = request.POST.get('maquiagem')
        pontos_sol = int(request.POST.get('reacao_sol', 0))
        base_produto = request.POST.get('base_produto')
        objective = request.POST.get('objetivo')
        
        # 2. Lógica para definir o Fototipo baseado na resposta do sol
        fototipo_calculado = pontos_sol + 1

        # 3. Salva as informações reais vinculadas ao usuário logado
        if request.user.is_authenticated:
            # Busca um perfil existente ou cria um novo para este usuário
            perfil, created = PerfilDermatologico.objects.get_or_create(
                usuario=request.user,
                defaults={
                    'idade': int(idade) if idade else 0,
                    'tipo_pele': tipo_pele or 'normal',
                    'alergias': alergias or '',
                    'objetivo': objective or 'Melhorar a pele',
                    'prefere_creme_ou_gel': base_produto if base_produto in ('creme', 'gel') else 'gel',
                    'usa_maquiagem_diariamente': maquiagem == '1',
                    'porcentagem_saude': 75,
                    'fototipo': pontos_sol + 1,
                }
            )

            perfil.idade = int(idade) if idade else perfil.idade
            perfil.tipo_pele = tipo_pele or perfil.tipo_pele
            perfil.alergias = alergias or perfil.alergias
            perfil.usa_maquiagem_diariamente = maquiagem == '1'
            perfil.fototipo = pontos_sol + 1
            perfil.objetivo = objective or perfil.objetivo
            perfil.prefere_creme_ou_gel = base_produto if base_produto in ('creme', 'gel') else perfil.prefere_creme_ou_gel

            # como iremos calcular a porcentagem de saúde?
            perfil.porcentagem_saude = 75

            # Salva tudo no banco de dados
            perfil.save()

        return redirect('dashboard')  # Redireciona para o Dashboard

    return render(request, 'core/questionario.html')

def tela_sucesso(request):
    return render(request, 'core/sucesso.html')


# View do Dashboard puxando dados do MySQL
def dashboard_view(request):
    # Se o usuário estiver logado, pegamos o perfil dele
    if request.user.is_authenticated:
        perfil = PerfilDermatologico.objects.filter(usuario=request.user).first()
    else:
        # Caso não esteja logado (acesso de teste), pega o primeiro cadastrado
        perfil = PerfilDermatologico.objects.first()

    rotina_manha = []
    rotina_noite = []
    if perfil:
        rotina_manha = [
            {
                'class': 'completed',
                'title': 'Limpeza Suave',
                'description': f'Rotina de limpeza diária para pele {perfil.tipo_pele}',
                'time': '08:00',
                'action': None,
                'icon': 'fa-check',
            },
            {
                'class': 'action-required' if perfil.porcentagem_saude < 80 else 'completed',
                'title': 'Hidratação & Tratamento',
                'description': f'Sérum recomendado para objetivo "{perfil.objetivo}"',
                'time': None if perfil.porcentagem_saude < 80 else '19:00',
                'action': 'Fazer agora' if perfil.porcentagem_saude < 80 else None,
                'icon': 'fa-check' if perfil.porcentagem_saude >= 80 else None,
            },
            {
                'class': 'pending' if perfil.fototipo and perfil.fototipo < 5 else 'completed',
                'title': 'Proteção Solar',
                'description': f'FPS 50+ para fototipo {perfil.fototipo or "1"}',
                'time': '12:00' if perfil.fototipo and perfil.fototipo < 5 else 'Já feito',
                'action': None,
                'icon': 'fa-check' if perfil.fototipo and perfil.fototipo >= 5 else None,
            },
        ]
        rotina_noite = [
            {
                'class': 'completed',
                'title': 'Remoção de Maquiagem',
                'description': 'Demaquilante suave antes de dormir',
                'time': '21:00',
                'action': None,
                'icon': 'fa-check',
            },
            {
                'class': 'completed',
                'title': 'Tratamento Noturno',
                'description': f'Sérum calmante para {perfil.tipo_pele}',
                'time': '21:30',
                'action': None,
                'icon': 'fa-check',
            },
            {
                'class': 'pending',
                'title': 'Hidratação Profunda',
                'description': 'Creme nutritivo para reparar enquanto dorme',
                'time': '22:00',
                'action': 'Aplicar agora',
                'icon': None,
            },
        ]

    context = {
        'perfil': perfil,
        'rotina_manha': rotina_manha,
        'rotina_noite': rotina_noite,
    }
    return render(request, 'core/dashboard.html', context)


# View para a Tela de Login
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