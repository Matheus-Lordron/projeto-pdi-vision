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

O projeto foi estruturado seguindo o padrão arquitetural **MVC (Model-View-Controller)** com foco em Programação Orientada a Objetos (POO). O Model (`nucleo/`) não depende da interface:

```text
projeto_pdi_vision/
├── nucleo/           # Model: vetor de Mats, Pipeline, classe base abstrata Operacao e leitura/gravação de imagens
├── operacoes/        # Implementações concretas dos algoritmos (OpenCV + NumPy), agrupadas pelo tema da aula
├── interface/        # View & Controller: Interface gráfica modular em PyQt6
├── main.py           # Ponto de entrada
└── requirements.txt  # Dependências (NumPy, OpenCV, PyQt6)
```

### Vetor de Mats

Todo o histórico do processamento fica em um **vetor de Mats** (`nucleo/vetor_mats.py`), equivalente ao `vector<Mat>` do OpenCV em C++:

- `Mat[0]` é a imagem original (lida com `imread`).
- `Mat[i]` é a saída da etapa *i* do pipeline (`nucleo/pipeline.py`).
- Por padrão a etapa *i* lê `Mat[i-1]`, mas pode ler qualquer `Mat[k]` anterior. Assim dá para reproduzir os exemplos da aula, como erosão e dilatação da mesma imagem seguidas de `dilatação − erosão` (gradiente morfológico).
- Quando um parâmetro da etapa *k* muda, só `Mat[k..n]` são recalculados; os anteriores são reaproveitados.

### Adicionando uma operação

Basta herdar de `nucleo.operacao.Operacao`, declarar os parâmetros em `parametros`, implementar `aplicar` (o processamento) e registrá-la em `operacoes/__init__.py`. A interface monta os controles sozinha.

---

## ✅ Requisitos do trabalho

| Requisito | Onde está implementado |
|---|---|
| Vetor de Mats | `nucleo/vetor_mats.py` (`VetorMats`) e `nucleo/pipeline.py` (`Pipeline`) |
| Conversão de cor | `operacoes/cor.py`: `cvtColor` (GRAY, HSV, HLS, Lab, Luv, XYZ, YCrCb), `split`/`merge`, fórmulas de cinza |
| Filtro (suavização/realce) | `operacoes/suavizacao.py`: `blur`, `GaussianBlur`, `medianBlur`, `bilateralFilter`; `operacoes/realce.py`: brilho/contraste, negativo, alargamento de contraste, `equalizeHist` |
| Detector de borda | `operacoes/bordas.py`: `Sobel`, `Laplacian`, `Canny`, Prewitt, Roberts, Kirsch e máscaras passa-alta (`filter2D`) |
| Binarização | `operacoes/limiarizacao.py`: `threshold` (incl. Otsu e Triângulo), `adaptiveThreshold`, `inRange` |
| Morfologia matemática | `operacoes/morfologia.py`: `erode`, `dilate`, `morphologyEx` (abertura, fechamento, gradiente, top-hat, black-hat) |
| Extra | `operacoes/entre_mats.py`: aritmética e lógica entre dois Mats do vetor |

---

## ▶️ Como executar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
python main.py                    # ou: python main.py caminho/da/imagem.png
```

## 🧭 Como usar

1. **Abra uma imagem** (Ctrl+O ou arrastando o arquivo para a janela). Ela vira o `Mat[0]`.
2. **Adicione operações** com duplo clique no catálogo à esquerda. A nova etapa entra logo depois do Mat selecionado e gera um novo Mat.
3. **Selecione um Mat** no vetor (faixa inferior) para vê-lo e ajustar os parâmetros da etapa que o gerou. Na equalização, o painel também mostra o histograma antes e depois.
4. **Entrada (src)**: escolha qual Mat do vetor a etapa lê (o anterior, por padrão).
5. **Comparar** (barra superior) mostra entrada × saída da etapa, ou original × Mat selecionado. Passando o mouse sobre a imagem, a barra de status mostra os valores do pixel em cada canal.
6. **Salvar Mat** (Ctrl+S) ou **Salvar todos** (Ctrl+Shift+S) grava os Mats como arquivos.
