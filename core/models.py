from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class PerfilDermatologico(models.Model):
    # Conecta o perfil ao usuário criado no cadastro
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Dados do questionário
    idade = models.IntegerField()
    TIPO_PELE_CHOICES = [
        ('oleosa', 'Oleosa'),
        ('seca', 'Seca'),
        ('mista', 'Mista'),
        ('normal', 'Normal'),
    ]
    tipo_pele = models.CharField(max_length=10, choices=TIPO_PELE_CHOICES)
    alergias = models.TextField(blank=True, null=True)
    objetivo = models.CharField(max_length=200)
    prefere_creme_ou_gel = models.CharField(max_length=10, choices=[('creme', 'Creme'), ('gel', 'Gel')])
    usa_maquiagem_diariamente = models.BooleanField(default=False)
    
    # Dados calculados pelo sistema posteriormente
    porcentagem_saude = models.IntegerField(default=50)
    fototipo = models.IntegerField(blank=True, null=True) # Escala de 1 a 6