import pygame
import math
import random
import numpy as np

# -------------------------------------------------
# CONFIGURAÇÕES GERAIS E MODO DE JOGO
# -------------------------------------------------
LARGURA_TELA = 800
ALTURA_TELA = 600
GRAVIDADE = 9.8              # aceleração da gravidade
RAIO_EXPLOSAO = 30           # raio da explosão
DRAG_COEFF = 0.05            # resistência do ar
MAGNUS_COEFF = 5.0           # efeito Magnus
HOMING_ACCEL = 30.0          # aceleração para mísseis guiados

# Força máxima aumentada para 200
FORCA_MIN = 10
FORCA_MAX = 200

# Modo de jogo: "campaign", "multiplayer" ou "challenge"
GAME_MODE = None  # será definido no menu inicial

# -------------------------------------------------
# INICIALIZAÇÃO DO PYGAME, ÁUDIO E VARIÁVEIS GLOBAIS
# -------------------------------------------------
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Tanks 2D - Evolução")
clock = pygame.time.Clock()

# Cores
BRANCO   = (255, 255, 255)
PRETO    = (0, 0, 0)
VERDE    = (0, 255, 0)
VERMELHO = (255, 0, 0)
AZUL     = (0, 0, 255)
AMARELO  = (255, 255, 0)
CINZA    = (100, 100, 100)
MARROM   = (139, 69, 19)

# Variável global de vento (que pode mudar dinamicamente)
wind_x = 0

# Parâmetros de campanha
level = 1
level_start = True
level_start_timer = 3  # tempo para exibir a tela de nível
narratives = {
    1: "Bem-vindo à batalha!",
    2: "A luta esquenta!",
    3: "Você está ficando forte!",
    4: "Desafios maiores à frente!",
    5: "A vitória está próxima!",
    # pode ser expandido conforme necessário
}

# -------------------------------------------------
# FUNÇÕES DE ÁUDIO
# -------------------------------------------------
def criar_som(frequencia, duracao, volume=0.5, taxa_amostragem=44100):
    t = np.linspace(0, duracao, int(taxa_amostragem * duracao), endpoint=False)
    onda = volume * np.sin(2 * math.pi * frequencia * t)
    onda_int = np.int16(onda * 32767)
    onda_stereo = np.column_stack((onda_int, onda_int))
    return pygame.sndarray.make_sound(onda_stereo)

som_explosao = criar_som(150, 0.5, volume=0.5)
som_tiro     = criar_som(500, 0.1, volume=0.5)
# Para música de fundo, poderíamos usar pygame.mixer.music.load("arquivo.mp3")
# mas aqui deixaremos como placeholder.

# -------------------------------------------------
# TERRENO DIVERSIFICADO (com tipo)
# -------------------------------------------------
def generate_terrain():
    # Gera uma lista de pontos: (x, y, tipo)
    # Tipo: "normal" (70%), "mud" (20%) e "rock" (10%)
    points = []
    base = ALTURA_TELA - 50
    y = base
    for x in range(0, LARGURA_TELA + 1, 10):
        y += random.randint(-5, 5)
        y = max(ALTURA_TELA - 150, min(y, ALTURA_TELA - 30))
        tipo = random.choices(["normal", "mud", "rock"], weights=[70,20,10])[0]
        points.append((x, y, tipo))
    return points

terrain = generate_terrain()

def get_ground_height(x):
    # Interpola a altura do terreno ignorando o tipo
    if x <= 0:
        return terrain[0][1]
    if x >= LARGURA_TELA:
        return terrain[-1][1]
    idx = int(x // 10)
    x1, y1, _ = terrain[idx]
    x2, y2, _ = terrain[idx+1]
    t_interp = (x - x1) / (x2 - x1)
    return y1 + t_interp * (y2 - y1)

def get_terrain_type(x):
    # Retorna o tipo do ponto mais próximo
    idx = int(x // 10)
    return terrain[min(idx, len(terrain)-1)][2]

def draw_terrain(surface):
    pts = [(x, y) for (x, y, _) in terrain]
    pts.append((LARGURA_TELA, ALTURA_TELA))
    pts.append((0, ALTURA_TELA))
    pygame.draw.polygon(surface, MARROM, pts)

def destroy_terrain(cx, cy, radius):
    global terrain
    new_terrain = []
    for (x, y, t) in terrain:
        dist = math.hypot(x - cx, y - cy)
        if dist < radius:
            delta = (radius - dist) / 2
            new_y = min(y + delta, ALTURA_TELA - 30)
            new_terrain.append((x, new_y, t))
        else:
            new_terrain.append((x, y, t))
    terrain = new_terrain

# -------------------------------------------------
# OBSTÁCULOS DINÂMICOS
# -------------------------------------------------
class Obstacle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
    def desenhar(self, surface):
        pygame.draw.rect(surface, CINZA, self.rect)

obstacles = []
def generate_obstacles(num):
    global obstacles
    obstacles = []
    for _ in range(num):
        w = random.randint(40, 80)
        h = random.randint(40, 80)
        x = random.randint(100, LARGURA_TELA - 100 - w)
        y_ground = get_ground_height(x)
        y = y_ground - h
        obstacles.append(Obstacle(x, y, w, h))

# -------------------------------------------------
# FUNÇÃO BALÍSTICA (para cálculo de ângulo)
# -------------------------------------------------
def calcular_angulo_balistico(shooter, alvo, forca):
    dx = alvo.x - shooter.x
    dy = shooter.y - alvo.y  # positivo se o alvo está acima
    if dx == 0:
        return 45
    g = GRAVIDADE * 10
    dx_abs = abs(dx)
    parte = forca**4 - g * (g * dx_abs**2 + 2 * dy * forca**2)
    if parte < 0:
        return 45 if dx >= 0 else 135
    angulo1 = math.degrees(math.atan((forca**2 + math.sqrt(parte)) / (g * dx_abs)))
    angulo2 = math.degrees(math.atan((forca**2 - math.sqrt(parte)) / (g * dx_abs)))
    angulo = min(angulo1, angulo2)
    if dx < 0:
        angulo = 180 - angulo
    return angulo

# -------------------------------------------------
# CLASSES DO JOGO
# -------------------------------------------------
class Tank:
    def __init__(self, x, cor, nome, forca=50):
        self.x = x
        self.cor = cor
        self.nome = nome
        self.angulo = 45              # em graus
        self.forca = forca            # entre FORCA_MIN e FORCA_MAX
        self.saude = 100
        self.width = 40
        self.height = 20
        self.weapon_type = "normal"   # pode ser "normal", "guided" ou "grenade"
        self.speed = 2                # velocidade base de movimento
        self.update_position()
        self.upgrades = {"health": 0, "force": 0, "speed": 0}
    def update_position(self):
        self.y = get_ground_height(self.x) - self.height/2
    def desenhar(self, surface):
        rect = pygame.Rect(self.x - self.width/2, self.y - self.height/2, self.width, self.height)
        pygame.draw.rect(surface, self.cor, rect)
        rad = math.radians(self.angulo)
        cannon_length = 30
        end_x = self.x + cannon_length * math.cos(rad)
        end_y = self.y - cannon_length * math.sin(rad)
        pygame.draw.line(surface, PRETO, (self.x, self.y), (end_x, end_y), 3)
        # HUD: saúde, forca, ângulo, arma e velocidade
        pygame.draw.rect(surface, PRETO, (self.x - 20, self.y - self.height, 40, 5))
        pygame.draw.rect(surface, VERDE, (self.x - 20, self.y - self.height, 40 * (self.saude/100), 5))
        font = pygame.font.SysFont(None, 18)
        hud = f"{self.nome}: {int(self.forca)}|{int(self.angulo)}° [{self.weapon_type}] Spd:{self.speed:.1f}"
        txt = font.render(hud, True, PRETO)
        surface.blit(txt, (self.x - 50, self.y - self.height - 20))

class Projetil:
    def __init__(self, x, y, angulo, forca, shooter, target=None, weapon_type="normal"):
        self.x = x
        self.y = y
        self.raio = 5
        self.ativo = True
        self.shooter = shooter
        rad = math.radians(angulo)
        self.vx = forca * math.cos(rad)
        self.vy = -forca * math.sin(rad)
        self.spin = random.uniform(-1, 1)
        self.weapon_type = weapon_type
        self.target = target  # usado para mísseis guiados
    def atualizar(self, dt):
        if not self.ativo:
            return
        self.vx += wind_x * dt
        self.vx *= (1 - DRAG_COEFF * dt)
        self.vy *= (1 - DRAG_COEFF * dt)
        v = math.hypot(self.vx, self.vy)
        if v != 0:
            mag_vx = -self.vy / v * MAGNUS_COEFF * self.spin * dt
            mag_vy = self.vx / v * MAGNUS_COEFF * self.spin * dt
            self.vx += mag_vx
            self.vy += mag_vy
        if self.weapon_type == "guided" and self.target is not None:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist != 0:
                desired_vx = (dx/dist) * math.hypot(self.vx, self.vy)
                desired_vy = (dy/dist) * math.hypot(self.vx, self.vy)
                self.vx += (desired_vx - self.vx) * HOMING_ACCEL * dt
                self.vy += (desired_vy - self.vy) * HOMING_ACCEL * dt
        self.vy += GRAVIDADE * dt * 10
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0 or self.x > LARGURA_TELA or self.y < 0 or self.y > ALTURA_TELA:
            self.ativo = False
        for obs in obstacles:
            if obs.rect.collidepoint(self.x, self.y):
                self.ativo = False
                break
    def desenhar(self, surface):
        if self.ativo:
            pygame.draw.circle(surface, PRETO, (int(self.x), int(self.y)), self.raio)

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.raio = random.randint(2, 4)
        self.cor = random.choice([VERMELHO, AMARELO, (255,128,0)])
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.tempo_vida = random.uniform(0.5, 1.0)
    def atualizar(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.tempo_vida -= dt
        self.vy += GRAVIDADE * dt * 10
    def desenhar(self, surface):
        if self.tempo_vida > 0:
            pygame.draw.circle(surface, self.cor, (int(self.x), int(self.y)), self.raio)

class PowerUp:
    def __init__(self, x, y, tipo):
        self.x = x
        self.y = y
        self.tipo = tipo  # 'health', 'force', 'weapon', 'armor' ou 'speed'
        self.ativo = True
        self.raio = 10
    def desenhar(self, surface):
        if self.ativo:
            if self.tipo == 'health':
                cor = AZUL
            elif self.tipo == 'force':
                cor = AMARELO
            elif self.tipo == 'armor':
                cor = CINZA
            elif self.tipo == 'speed':
                cor = (0, 255, 255)
            else:
                cor = (128, 0, 128)
            pygame.draw.circle(surface, cor, (int(self.x), int(self.y)), self.raio)

powerups = []
powerup_timer = 0

# -------------------------------------------------
# FUNÇÃO DE NOVO NÍVEL (CAMPANHA E CHALLENGE)
# -------------------------------------------------
def new_level(lvl):
    global terrain, wind_x, obstacles
    terrain = generate_terrain()
    # Vento aumenta com o nível e pode mudar durante o nível
    wind_x = random.uniform(-lvl * 5, lvl * 5)
    generate_obstacles(min(3 + lvl, 8))

# -------------------------------------------------
# MENU INICIAL PARA SELEÇÃO DE MODO
# -------------------------------------------------
def menu_inicial():
    global GAME_MODE
    selecionado = None
    fonte = pygame.font.SysFont(None, 48)
    while selecionado is None:
        tela.fill(BRANCO)
        titulo = fonte.render("Tanks 2D - Selecione o Modo", True, PRETO)
        op1 = fonte.render("1 - Campanha", True, PRETO)
        op2 = fonte.render("2 - Multiplayer Local", True, PRETO)
        op3 = fonte.render("3 - Challenge (em breve)", True, PRETO)
        tela.blit(titulo, (LARGURA_TELA//2 - titulo.get_width()//2, 100))
        tela.blit(op1, (LARGURA_TELA//2 - op1.get_width()//2, 200))
        tela.blit(op2, (LARGURA_TELA//2 - op2.get_width()//2, 260))
        tela.blit(op3, (LARGURA_TELA//2 - op3.get_width()//2, 320))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    GAME_MODE = "campaign"
                    return
                elif event.key == pygame.K_2:
                    GAME_MODE = "multiplayer"
                    return
                elif event.key == pygame.K_3:
                    GAME_MODE = "challenge"
                    return

menu_inicial()
MULTIPLAYER = (GAME_MODE == "multiplayer")
# Para "challenge", podemos tratá-lo como campanha com dificuldade extra (não detalhado aqui)

# -------------------------------------------------
# INICIALIZAÇÃO DOS TANQUES
# -------------------------------------------------
if MULTIPLAYER:
    tank1 = Tank(100, VERDE, "Jogador 1", forca=50)
    tank2 = Tank(LARGURA_TELA - 100, VERMELHO, "Jogador 2", forca=50)
else:
    tank1 = Tank(100, VERDE, "Jogador", forca=50)
    tank2 = Tank(LARGURA_TELA - 100, VERMELHO, "Inimigo", forca=50)

# -------------------------------------------------
# VARIÁVEIS GLOBAIS DO JOGO
# -------------------------------------------------
projetil_atual = None
lista_particulas = []
turno = 1  # 1: turno do jogador; 2: turno do inimigo (IA ou segundo jogador)
enemy_ai_adjust_delay = 0

if GAME_MODE in ["campaign", "challenge"]:
    new_level(level)
    level_start = True
    level_start_timer = 3

# -------------------------------------------------
# LOOP PRINCIPAL DO JOGO
# -------------------------------------------------
while True:
    dt = clock.tick(60) / 1000.0

    # Tela de início de nível (para campanha/challenge)
    if GAME_MODE in ["campaign", "challenge"] and level_start:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                level_start = False
        tela.fill(BRANCO)
        fonte_grande = pygame.font.SysFont(None, 48)
        level_text = fonte_grande.render(f"Level {level}", True, PRETO)
        narrative = narratives.get(level, "Prepare-se!")
        narrative_text = fonte_grande.render(narrative, True, PRETO)
        tela.blit(level_text, (LARGURA_TELA//2 - level_text.get_width()//2, ALTURA_TELA//2 - level_text.get_height()))
        tela.blit(narrative_text, (LARGURA_TELA//2 - narrative_text.get_width()//2, ALTURA_TELA//2))
        pygame.display.flip()
        level_start_timer -= dt
        if level_start_timer <= 0:
            level_start = False
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        # Disparo e ajuste de ângulo/arma
        if MULTIPLAYER:
            if turno == 1:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and projetil_atual is None:
                        rad = math.radians(tank1.angulo)
                        proj_x = tank1.x + 30 * math.cos(rad)
                        proj_y = tank1.y - 30 * math.sin(rad)
                        projetil_atual = Projetil(proj_x, proj_y, tank1.angulo, tank1.forca, tank1, target=tank2, weapon_type=tank1.weapon_type)
                        som_tiro.play()
                    if event.key == pygame.K_UP:
                        tank1.angulo = min(90, tank1.angulo + 1)
                    if event.key == pygame.K_DOWN:
                        tank1.angulo = max(0, tank1.angulo - 1)
                    if event.key == pygame.K_v:
                        # Cicla entre "normal" -> "guided" -> "grenade" -> "normal"
                        if tank1.weapon_type == "normal":
                            tank1.weapon_type = "guided"
                        elif tank1.weapon_type == "guided":
                            tank1.weapon_type = "grenade"
                        else:
                            tank1.weapon_type = "normal"
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RCTRL and projetil_atual is None:
                        rad = math.radians(tank2.angulo)
                        proj_x = tank2.x + 30 * math.cos(rad)
                        proj_y = tank2.y - 30 * math.sin(rad)
                        projetil_atual = Projetil(proj_x, proj_y, tank2.angulo, tank2.forca, tank2, target=tank1, weapon_type=tank2.weapon_type)
                        som_tiro.play()
                    if event.key == pygame.K_w:
                        tank2.angulo = min(90, tank2.angulo + 1)
                    if event.key == pygame.K_s:
                        tank2.angulo = max(0, tank2.angulo - 1)
                    if event.key == pygame.K_SLASH:
                        if tank2.weapon_type == "normal":
                            tank2.weapon_type = "guided"
                        elif tank2.weapon_type == "guided":
                            tank2.weapon_type = "grenade"
                        else:
                            tank2.weapon_type = "normal"
        else:
            if turno == 1:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and projetil_atual is None:
                        rad = math.radians(tank1.angulo)
                        proj_x = tank1.x + 30 * math.cos(rad)
                        proj_y = tank1.y - 30 * math.sin(rad)
                        projetil_atual = Projetil(proj_x, proj_y, tank1.angulo, tank1.forca, tank1, target=tank2, weapon_type=tank1.weapon_type)
                        som_tiro.play()
                    if event.key == pygame.K_UP:
                        tank1.angulo = min(90, tank1.angulo + 1)
                    if event.key == pygame.K_DOWN:
                        tank1.angulo = max(0, tank1.angulo - 1)
                    if event.key == pygame.K_v:
                        if tank1.weapon_type == "normal":
                            tank1.weapon_type = "guided"
                        elif tank1.weapon_type == "guided":
                            tank1.weapon_type = "grenade"
                        else:
                            tank1.weapon_type = "normal"

    # -------------------------------------------------
    # PROCESSAMENTO CONTÍNUO (MOVIMENTO E AJUSTE DE FORÇA)
    # -------------------------------------------------
    keys = pygame.key.get_pressed()
    # Movimento e ajuste de força (para jogador)
    if turno == 1:
        # Movimento: considere o tipo do terreno para ajustar velocidade
        tipo = get_terrain_type(tank1.x)
        if tipo == "mud":
            efetive_speed = tank1.speed * 0.5
        elif tipo == "rock":
            efetive_speed = tank1.speed * 0.8
        else:
            efetive_speed = tank1.speed
        if keys[pygame.K_a]:
            tank1.x = max(0, tank1.x - efetive_speed)
            tank1.update_position()
        if keys[pygame.K_d]:
            tank1.x = min(LARGURA_TELA, tank1.x + efetive_speed)
            tank1.update_position()
        if keys[pygame.K_z]:
            tank1.forca = max(FORCA_MIN, tank1.forca - 50 * dt)
        if keys[pygame.K_x]:
            tank1.forca = min(FORCA_MAX, tank1.forca + 50 * dt)
    else:
        if MULTIPLAYER:
            tipo = get_terrain_type(tank2.x)
            if tipo == "mud":
                efetive_speed = tank2.speed * 0.5
            elif tipo == "rock":
                efetive_speed = tank2.speed * 0.8
            else:
                efetive_speed = tank2.speed
            if keys[pygame.K_LEFT]:
                tank2.x = max(0, tank2.x - efetive_speed)
                tank2.update_position()
            if keys[pygame.K_RIGHT]:
                tank2.x = min(LARGURA_TELA, tank2.x + efetive_speed)
                tank2.update_position()
            if keys[pygame.K_COMMA]:
                tank2.forca = max(FORCA_MIN, tank2.forca - 50 * dt)
            if keys[pygame.K_PERIOD]:
                tank2.forca = min(FORCA_MAX, tank2.forca + 50 * dt)
        else:
            # No turno do inimigo (IA) em campanha, ele se move apenas em seu turno
            move_speed = 50 * dt
            if tank2.saude >= 70:
                # Se saudável, se posiciona próximo (mas não exatamente igual) ao jogador
                if tank2.x > tank1.x + 20:
                    tank2.x -= move_speed
                elif tank2.x < tank1.x - 20:
                    tank2.x += move_speed
            else:
                # Se com pouca saúde, recua
                if tank2.x > tank1.x:
                    tank2.x += move_speed
                else:
                    tank2.x -= move_speed
            tank2.x = max(0, min(LARGURA_TELA, tank2.x))
            tank2.update_position()

    # -------------------------------------------------
    # IA DO INIMIGO (no modo campanha)
    # -------------------------------------------------
    if not MULTIPLAYER and turno == 2 and projetil_atual is None:
        desired_angle = calcular_angulo_balistico(tank2, tank1, tank2.forca)
        if abs(tank2.angulo - desired_angle) > 1:
            if tank2.angulo < desired_angle:
                tank2.angulo += 1
            else:
                tank2.angulo -= 1
        else:
            tank2.angulo = desired_angle
            rad = math.radians(tank2.angulo)
            proj_x = tank2.x + 30 * math.cos(rad)
            proj_y = tank2.y - 30 * math.sin(rad)
            projetil_atual = Projetil(proj_x, proj_y, tank2.angulo, tank2.forca, tank2, target=tank1, weapon_type=tank2.weapon_type)
            som_tiro.play()
        # Comportamento extra: ocasionalmente trocar a arma
        if random.random() < 0.005:
            tank2.weapon_type = random.choice(["normal", "guided", "grenade"])

    # -------------------------------------------------
    # ATUALIZAÇÃO DO PROJÉTIL
    # -------------------------------------------------
    if projetil_atual:
        projetil_atual.atualizar(dt)
        # Verifica colisão com tanques
        for t in [tank1, tank2]:
            dist = math.hypot(projetil_atual.x - t.x, projetil_atual.y - t.y)
            if dist <= RAIO_EXPLOSAO:
                # Se for granada, causa mais dano
                if projetil_atual.weapon_type == "grenade":
                    dano = 30
                    # E pode gerar sub-explosões (simuladas com partículas extras)
                    for _ in range(10):
                        lista_particulas.append(Particle(projetil_atual.x, projetil_atual.y))
                else:
                    dano = 20
                    for _ in range(30):
                        lista_particulas.append(Particle(projetil_atual.x, projetil_atual.y))
                t.saude = max(0, t.saude - dano)
                projetil_atual.ativo = False
                som_explosao.play()
                destroy_terrain(projetil_atual.x, projetil_atual.y, RAIO_EXPLOSAO)
                break
        # Colisão com o terreno
        ground_y = get_ground_height(projetil_atual.x)
        if projetil_atual.y >= ground_y:
            projetil_atual.ativo = False
            for _ in range(30):
                lista_particulas.append(Particle(projetil_atual.x, projetil_atual.y))
            som_explosao.play()
            destroy_terrain(projetil_atual.x, projetil_atual.y, RAIO_EXPLOSAO)
        if not projetil_atual.ativo:
            projetil_atual = None
            turno = 2 if turno == 1 else 1

    # -------------------------------------------------
    # ATUALIZAÇÃO DAS PARTÍCULAS
    # -------------------------------------------------
    for p in lista_particulas[:]:
        p.atualizar(dt)
        if p.tempo_vida <= 0:
            lista_particulas.remove(p)

    # -------------------------------------------------
    # SPWAN DE POWER-UPS (inclui novos tipos: armor e speed)
    # -------------------------------------------------
    powerup_timer += dt
    if powerup_timer > 5:
        powerup_timer = 0
        tipo = random.choice(['health', 'force', 'weapon', 'armor', 'speed'])
        x = random.randint(50, LARGURA_TELA - 50)
        y = get_ground_height(x) - 15
        powerups.append(PowerUp(x, y, tipo))
    
    for pu in powerups[:]:
        if pu.ativo:
            for t in [tank1, tank2]:
                if math.hypot(t.x - pu.x, t.y - pu.y) < 20:
                    pu.ativo = False
                    if pu.tipo == 'health':
                        t.saude = min(100, t.saude + 20)
                    elif pu.tipo == 'force':
                        t.forca = min(FORCA_MAX, t.forca + 10)
                    elif pu.tipo == 'armor':
                        t.saude = min(150, t.saude + 20)  # aumenta saúde máxima
                    elif pu.tipo == 'speed':
                        t.speed += 0.5  # aumenta a velocidade de movimento
                    elif pu.tipo == 'weapon':
                        # Alterna para um tipo aleatório de arma
                        t.weapon_type = random.choice(["normal", "guided", "grenade"])
                    powerups.remove(pu)
                    break

    # -------------------------------------------------
    # FIM DE NÍVEL (para campanha/challenge)
    # -------------------------------------------------
    if GAME_MODE in ["campaign", "challenge"]:
        if tank2.saude <= 0:
            level += 1
            tank2.saude = 100 + level * 10
            tank2.x = LARGURA_TELA - 100
            tank2.update_position()
            new_level(level)
            turno = 1
            level_start = True
            level_start_timer = 3
        if tank1.saude <= 0:
            fonte = pygame.font.SysFont(None, 72)
            tela.fill(BRANCO)
            game_over_text = fonte.render("Game Over!", True, VERMELHO)
            tela.blit(game_over_text, (LARGURA_TELA//2 - game_over_text.get_width()//2, ALTURA_TELA//2 - game_over_text.get_height()//2))
            pygame.display.flip()
            pygame.time.wait(3000)
            level = 1
            tank1.saude = 100
            tank2.saude = 100
            tank1.x = 100
            tank2.x = LARGURA_TELA - 100
            tank1.update_position()
            tank2.update_position()
            new_level(level)
            turno = 1
            level_start = True
            level_start_timer = 3

    # -------------------------------------------------
    # ATUALIZAÇÃO DINÂMICA DO VENTO (opcional)
    # -------------------------------------------------
    # Aqui o vento pode oscilar suavemente
    wind_x += random.uniform(-0.5, 0.5) * dt
    wind_x = max(-level*5, min(wind_x, level*5))
    
    # -------------------------------------------------
    # RENDERIZAÇÃO
    # -------------------------------------------------
    tela.fill(BRANCO)
    draw_terrain(tela)
    for obs in obstacles:
        obs.desenhar(tela)
    for pu in powerups:
        pu.desenhar(tela)
    tank1.desenhar(tela)
    tank2.desenhar(tela)
    if projetil_atual:
        projetil_atual.desenhar(tela)
    for p in lista_particulas:
        p.desenhar(tela)
    # HUD aprimorado
    fonte_hud = pygame.font.SysFont(None, 24)
    hud_text = fonte_hud.render(f"Level: {level}  Wind: {wind_x:.1f}  Mode: {GAME_MODE.upper()}", True, PRETO)
    tela.blit(hud_text, (10, 10))
    turno_text = fonte_hud.render("Turno: " + ("Jogador" if turno == 1 else ("Inimigo (IA)" if GAME_MODE != "multiplayer" else "Jogador 2")), True, PRETO)
    tela.blit(turno_text, (10, 30))
    pygame.display.flip()

