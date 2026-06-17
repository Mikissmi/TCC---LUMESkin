from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import PerfilDermatologico 
import requests
import time
import json

# Configurações da API YouCam (PerfectCorp)
YOUCAM_URL = 'https://yce-api-01.makeupar.com/s2s/v2.1/task/skin-analysis'
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer SEU_TOKEN_AQUI" # <-- Insira o seu Token aqui
}

def comunicar_youcam_api(foto_arquivo):
    # Alterado json.dumps para enviar o enable_mask_overlay como TRUE
    dados_config = {
        "dst_actions": json.dumps([
            "acne", "eye_bag", "moisture", "pore", "redness",
            "texture", "skin_type", "dark_circle_v2", "oiliness",
            "radiance", "age_spot"
        ]),
        # ATIVANDO O DESENHO AUTOMÁTICO DA IA:
        "miniserver_args": json.dumps({ "enable_mask_overlay": True }), 
        "format": "json",
        "pf_camera_kit": "False"
    }
    
    files = {
        'src_file': (foto_arquivo.name, foto_arquivo.read(), foto_arquivo.content_type)
    }
    
    try:
        resposta = requests.post(YOUCAM_URL, headers=HEADERS, data=dados_config, files=files, timeout=15)
        if not resposta.ok:
            return None
            
        task_id = resposta.json().get('data', {}).get('task_id')
        if not task_id:
            return None
            
        for _ in range(15):
            time.sleep(2)
            checagem = requests.get(f"{YOUCAM_URL}/{task_id}", headers=HEADERS, timeout=10)
            
            if checagem.ok:
                payload = checagem.json()
                status = payload.get('data', {}).get('task_status')
                
                if status == 'success':
                    # Agora o 'results' conterá os dados textuais E o link da imagem com pontos!
                    return payload.get('data', {}).get('results')
                elif status == 'error':
                    break
    except Exception as e:
        print(f"[Erro YouCam API]: {e}")
        
    return None

def tela_cadastro(request):

    # 1. Verifica se o navegador está enviando dados através de um formulário (POST)
    if request.method == "POST":
        # 2. Captura o valor digitado no campo <input name="nome"> do HTML
        nome = request.POST.get('nome')
        # 3. Captura o valor digitado no campo <input name="email"> do HTML
        email = request.POST.get('email')
        # 4. Captura o valor digitado no campo <input name="senha"> do HTML
        senha = request.POST.get('senha') 
        
        # 5. Cria e salva um novo registro na tabela de usuários padrão do Django (auth_user).
        # Note que aqui você definiu que o 'username' (login) do usuário será o próprio e-mail dele.
        novo_usuario = User.objects.create_user(
            username=email, 
            email=email, 
            password=senha, 
            first_name=nome
        )
        # 6. Confirma e consolida a gravação do novo usuário dentro do banco de dados
        novo_usuario.save()
    
        # 7. Autentica o usuário recém-criado na sessão do navegador (faz o login automático)
        auth_login(request, novo_usuario)
        # 8. Redireciona o usuário logado para a página do questionário (URL name='questionario')
        return redirect('questionario')
        
        # 9. Se a requisição NÃO for POST (ou seja, se for um acesso normal via GET para carregar a página),
        #renderiza e exibe a tela com o formulário de cadastro limpo.
    return render(request, 'core/cadastro.html')


def tela_questionario(request):
    if request.method == "POST":
        # 1. Pega TODAS as respostas do formulário HTML
        idade = request.POST.get('idade')
        tipo_pele = request.POST.get('tipo_pele')
        alergias = request.POST.get('alergias')
        descricao_alergia = request.POST.get('descricaoalergia')
        maquiagem = request.POST.get('maquiagem')
        pontos_sol = int(request.POST.get('reacao_sol', 0))
        base_produto = request.POST.get('base_produto')
        objective = request.POST.get('objetivo')
        
        # Verifica se o usuário aceitou fazer o escaneamento opcional
        quer_escanear = request.POST.get('quer_escanear') == 'sim'
        
        porcentagem_calculada = 75  # Valor padrão caso ele NÃO queira escanear
        
        # 2. SÓ CHAMA A API SE O USUÁRIO OPTOU POR ISSO E ENVIOU O ARQUIVO
        if quer_escanear:
            # Captura o arquivo real vindo da memória do upload do Django
            foto_usuario = request.FILES.get('foto_rosto')
            
            if foto_usuario:
                # Passa o arquivo legítimo (UploadedFile) para a API, evitando o AttributeError (.name)
                resultados_ia = comunicar_youcam_api(foto_usuario)
                
                if resultados_ia:
                    try:
                        # Mapeia os dados retornados pela YouCam API
                        acne_score = resultados_ia.get('acne', {}).get('score', 80)
                        pore_score = resultados_ia.get('pore', {}).get('score', 80)
                        oil_score = resultados_ia.get('oiliness', {}).get('score', 80)
                        
                        # Faz uma média aritmética simples para o painel
                        porcentagem_calculada = int((acne_score + pore_score + oil_score) / 3)
                    except Exception:
                        porcentagem_calculada = 75
            else:
                # Caso o usuário tenha marcado 'sim' mas não tenha selecionado nenhum arquivo
                porcentagem_calculada = 75

        # 3. Salva ou atualiza as informações no banco de dados (MySQL)
        if request.user.is_authenticated:
            perfil, created = PerfilDermatologico.objects.get_or_create(
                usuario=request.user,
                defaults={
                    'idade': int(idade) if idade else 0,
                    'tipo_pele': tipo_pele or 'normal',
                    'alergias': alergias or '',
                    'objetivo': objective or 'Melhorar a pele',
                    'prefere_creme_ou_gel': base_produto if base_produto in ('creme', 'gel') else 'gel',
                    'usa_maquiagem_diariamente': maquiagem == '1',
                    'porcentagem_saude': porcentagem_calculada,
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
            perfil.porcentagem_saude = porcentagem_calculada
            
            perfil.save()

        return redirect('dashboard')

    return render(request, 'core/questionario.html')


def tela_sucesso(request):
    return render(request, 'core/sucesso.html')


def dashboard_view(request):
    if request.user.is_authenticated:
        perfil = PerfilDermatologico.objects.filter(usuario=request.user).first()
    else:
        perfil = PerfilDermatologico.objects.first()

    url_imagem_com_pontos = None

    if perfil and hasattr(perfil, 'dados_ia') and perfil.dados_ia:
        try:
            resultados_ia = json.loads(perfil.dados_ia)
            
            # Buscando a URL da imagem processada que a YouCam gerou.
            # Nota: Verifique no painel de respostas da API se a chave se chama exatamente 'overlay_image_url'
            url_imagem_com_pontos = resultados_ia.get('overlay_image_url') or resultados_ia.get('result_image_url')
            
        except Exception as e:
            print(f"Erro ao ler JSON da IA: {e}")

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
        'url_ia_workflow': url_imagem_com_pontos, # Passando a foto editada para o HTML
    }
    return render(request, 'core/dashboard.html', context)


def tela_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        usuario = authenticate(request, username=email, password=senha)
        
        if usuario is not None:
            auth_login(request, usuario)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'erro': 'Usuário ou senha incorretos'})
            
    return render(request, 'core/login.html')