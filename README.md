# PDI Vision Studio

Uma aplicação desktop interativa para **Processamento Digital de Imagens (PDI)** desenvolvida em **Python** e **PyQt6**, inspirada na arquitetura em pipeline modular do software *RoboRealm*.

---

## 🎯 Objetivo e Finalidade

O software foi concebido como projeto prático da disciplina de Processamento Digital de Imagens. Seu intuito principal é fornecer uma plataforma visual, não destrutiva e em tempo real para experimentação e encadeamento de algoritmos clássicos de visão computacional e PDI.

Diferente de scripts sequenciais convencionais, a ferramenta adota o conceito de **Pipeline Reativo**:
- A imagem de entrada é preservada de forma imutável na memória.
- As transformações são empilhadas em uma lista de operações sequenciais.
- O resultado de uma camada alimenta diretamente a camada subsequente.
- Permite reordenar camadas, desabilitar/habilitar filtros temporariamente e ajustar parâmetros matemáticos via interface gráfica com retorno visual instantâneo.

---

## 🏗️ Arquitetura do Sistema

O projeto foi estruturado seguindo o padrão arquitetural **MVC (Model-View-Controller)** com foco em Programação Orientada a Objetos (POO):

```text
projeto_pdi_vision/
├── core/             # Model: Pipeline, gerenciamento de estado e classe base abstrata
├── filters/          # Implementações concretas dos algoritmos (OpenCV + NumPy)
├── ui/               # View & Controller: Interface gráfica modular em PyQt6
└── utils/            # Conversores de dados (NumPy/OpenCV BGR <-> QPixmap RGB)
