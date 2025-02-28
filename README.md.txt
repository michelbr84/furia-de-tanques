# Fúria de Tanques

**Fúria de Tanques** é um jogo de tanques 2D desenvolvido em Python com a biblioteca Pygame. Mergulhe em batalhas intensas onde física realista, terrenos dinâmicos e uma variedade de armas se unem para proporcionar uma experiência única.

## Características

- **Física Realista:**  
  Simulação de gravidade, resistência do ar, efeito Magnus e vento dinâmico que influenciam a trajetória dos projéteis.

- **Terreno Dinâmico:**  
  Terrenos gerados proceduralmente com diferentes tipos (normal, lama e rocha) que afetam a movimentação dos tanques.

- **Variedade de Armas:**  
  Utilize munições normais, guiadas e granadas (com sub-explosões) para surpreender seus oponentes.

- **Power-Ups e Upgrades:**  
  Colete itens que aumentam saúde (incluindo “armor”), força, velocidade e alteram o tipo de arma do seu tanque.

- **Modos de Jogo:**  
  Escolha entre Campanha (com níveis progressivos e narrativa), Multiplayer Local ou o modo Challenge (em breve).

- **Efeitos Visuais e Sonoros:**  
  Explosões com partículas, sons dinâmicos e um HUD informativo que exibe dados dos tanques, vento, nível e muito mais.

- **IA Inimiga Aprimorada:**  
  Em modo Campanha, a inteligência artificial se movimenta, ajusta seu ângulo e força e adota estratégias de combate.

## Instalação

### Pré-requisitos

- Python 3.6 ou superior  
- [Pygame](https://www.pygame.org/)  
- [NumPy](https://numpy.org/)

### Instalando as Dependências

Você pode instalar as dependências necessárias via pip:

```bash
pip install pygame numpy
```

## Como Executar

Clone o repositório e execute o script principal:

```bash
git clone https://github.com/seu-usuario/furia-de-tanques.git
cd furia-de-tanques
python main.py
```

## Controles

### Modo Campanha (Single Player)

- **Movimentação:**  
  - `A` e `D` para mover o tanque para a esquerda e direita (a velocidade pode ser afetada pelo tipo do terreno).

- **Ajuste de Força:**  
  - `Z` para diminuir a força (pressione e segure para ajuste contínuo).  
  - `X` para aumentar a força (pressione e segure para ajuste contínuo; força máxima: 200).

- **Ajuste de Ângulo:**  
  - `Seta para cima` e `Seta para baixo` para alterar o ângulo do canhão.

- **Disparo:**  
  - `Espaço` para disparar o projétil.

- **Trocar Arma:**  
  - `V` para alternar entre os tipos de arma (normal, guiada, granada).

### Multiplayer Local

#### Jogador 1

- **Movimentação:** `A` e `D`  
- **Ajuste de Força:** `Z` (diminuir) e `X` (aumentar)  
- **Ajuste de Ângulo:** `Seta para cima` e `Seta para baixo`  
- **Disparo:** `Espaço`  
- **Trocar Arma:** `V`

#### Jogador 2

- **Movimentação:** `Seta para esquerda` e `Seta para direita`  
- **Ajuste de Força:** `,` (diminuir) e `.` (aumentar)  
- **Ajuste de Ângulo:** `W` e `S`  
- **Disparo:** `Ctrl direito`  
- **Trocar Arma:** `/`

## Estrutura do Projeto

```
furia-de-tanques/
├── main.py          # Script principal do jogo
├── README.md        # Este arquivo
├── assets/          # Recursos (sons, imagens, etc.) – se aplicável
└── LICENSE          # Licença do projeto
```

## Contribuindo

Contribuições são sempre bem-vindas! Se você deseja ajudar a melhorar o **Fúria de Tanques**, siga estes passos:

1. Faça um fork do repositório.
2. Crie uma branch para sua feature (`git checkout -b minha-feature`).
3. Realize as alterações desejadas e faça commits.
4. Envie um pull request com uma descrição detalhada das mudanças.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## Créditos

**Fúria de Tanques** foi desenvolvido utilizando Python, Pygame e NumPy. Agradecemos à comunidade open-source e a todos que contribuíram com ideias e feedback para tornar este projeto possível.

---

Divirta-se e que a Fúria de Tanques esteja com você!
```