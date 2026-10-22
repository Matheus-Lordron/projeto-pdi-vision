# PDI Vision

Ferramenta didática de processamento de imagens, inspirada no RoboRealm, feita para a
disciplina de Processamento de Imagens Aplicado à Agroindústria. Cada operação aplicada
gera um novo `Mat`, guardado em um **vetor de Mats** que funciona como histórico do
processamento.

## Como executar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
python main.py                    # ou: python main.py caminho/da/imagem.png
```

## Como usar

1. **Abra uma imagem** (Ctrl+O ou arrastando o arquivo para a janela). Ela vira o `Mat[0]`.
2. **Adicione operações** com duplo clique no catálogo à esquerda. A nova etapa entra logo
   depois do Mat selecionado e gera um novo Mat.
3. **Selecione um Mat** no vetor (faixa inferior) para vê-lo e ajustar os parâmetros da etapa
   que o gerou. O painel da direita mostra o código Python/OpenCV equivalente.
4. **Entrada (src)**: por padrão a etapa lê o Mat anterior, mas pode ler qualquer `Mat[k]`.
   Assim dá para reproduzir os exemplos da aula, como erosão e dilatação da mesma imagem
   seguidas de `dilatação − erosão` (gradiente morfológico).
5. **Comparar** (barra superior) mostra entrada × saída da etapa, ou original × Mat selecionado.
   Passando o mouse sobre a imagem, a barra de status mostra os valores do pixel em cada canal.
6. **Salvar Mat** (Ctrl+S) ou **Salvar todos** (Ctrl+Shift+S) grava os Mats como arquivos.

## Requisitos do trabalho

| Requisito | Onde está implementado |
|---|---|
| Vetor de Mats | `core/mat_vector.py` (`MatVector`) e `core/pipeline.py` (`Pipeline`) |
| Conversão de cor | `operations/color.py`: `cvtColor` (GRAY, HSV, HLS, Lab, Luv, XYZ, YCrCb), `split`/`merge`, fórmulas de cinza |
| Filtro (suavização/realce) | `operations/smoothing.py`: `blur`, `GaussianBlur`, `medianBlur`, `bilateralFilter`; `operations/enhancement.py`: brilho/contraste, negativo, alargamento de contraste, `equalizeHist` |
| Detector de borda | `operations/edges.py`: `Sobel`, `Laplacian`, `Canny`, Prewitt, Roberts, Kirsch e máscaras passa-alta (`filter2D`) |
| Binarização | `operations/threshold.py`: `threshold` (incl. Otsu e Triângulo), `adaptiveThreshold`, `inRange` |
| Morfologia matemática | `operations/morphology.py`: `erode`, `dilate`, `morphologyEx` (abertura, fechamento, gradiente, top-hat, black-hat) |
| Extra | `operations/algebraic.py`: aritmética e lógica entre dois Mats do vetor |

## Estrutura

```
core/         vetor de Mats, base das operações e pipeline (não depende da interface)
operations/   uma classe por operação, agrupadas pelo tema da aula
ui/           interface PyQt6 (catálogo, visualizador, parâmetros, vetor de Mats)
main.py       ponto de entrada
```

Para criar uma operação, basta herdar de `core.operation.Operation`, declarar os parâmetros
em `params`, implementar `apply` (o processamento) e `code` (o código exibido) e registrá-la
em `operations/__init__.py`. A interface monta os controles sozinha.
