"""Pipeline: lista ordenada de operações que preenche o vetor de Mats.

A etapa i grava sua saída em Mat[i]. Por padrão ela recebe Mat[i-1], mas pode
ler qualquer Mat[k] anterior (ex.: erosão e dilatação, ambas da imagem cinza,
seguidas de "dilatação − erosão"). Quando a etapa k muda, só Mat[k..n] são
recalculados; Mat[0..k-1] são reaproveitados.
"""

import numpy as np

from .mat_vector import MatEntry, MatVector
from .operation import INPUT_REF, Operation


class Pipeline:
    def __init__(self):
        self.steps: list[Operation] = []
        self.mats = MatVector()

    @property
    def has_image(self) -> bool:
        return not self.mats.empty()

    def set_source(self, mat: np.ndarray, label: str = "Original"):
        self.mats.clear()
        self.mats.push_back(mat, label, "GRAY" if mat.ndim == 2 else "BGR")
        self.run()

    def step(self, index: int) -> Operation:
        """Operação que gera Mat[index] (index >= 1)."""
        return self.steps[index - 1]

    def label(self, index: int) -> str:
        if index == 0:
            return self.mats.entry(0).label if self.has_image else "Original"
        return self.step(index).title()

    def entry(self, index: int) -> MatEntry | None:
        return self.mats.entry(index) if index < len(self.mats) else None

    def source_index(self, index: int) -> int:
        """Índice do Mat que a etapa ``index`` usa como entrada."""
        source = self.step(index).source
        return index - 1 if source == INPUT_REF else source

    def insert(self, index: int, op: Operation) -> int:
        """Insere ``op`` para gerar Mat[index]; as etapas seguintes andam uma posição."""
        index = max(1, min(index, len(self.steps) + 1))
        self.steps.insert(index - 1, op)
        self.run(index)
        return index

    def remove(self, index: int):
        del self.steps[index - 1]
        self.run(index)

    def move(self, index: int, delta: int) -> int:
        target = index + delta
        if not 1 <= target <= len(self.steps):
            return index
        self.steps[index - 1], self.steps[target - 1] = self.steps[target - 1], self.steps[index - 1]
        self.run(min(index, target))
        return target

    def clear(self):
        self.steps.clear()
        self.run()

    def run(self, first: int = 1):
        """(Re)processa a partir da etapa ``first``, reaproveitando Mat[0..first-1]."""
        if self.mats.empty():
            return
        first = max(1, min(first, len(self.mats)))
        self.mats.resize(first)
        for i in range(first, len(self.steps) + 1):
            op = self.steps[i - 1]
            previous = self.mats.entry(i - 1)
            dst, space = previous.mat, previous.space  # desativada/com erro: repassa Mat[i-1]
            op.error = op.info = None
            k = self.source_index(i)
            if op.enabled and not 0 <= k < i:
                op.error = f"A entrada Mat[{k}] não existe antes de Mat[{i}]; escolha outra entrada."
            elif op.enabled:
                src = self.mats.entry(k)
                try:
                    dst = op.run(src.mat, self.mats, src.space)
                    space = op.output_space(src.space, dst)
                except Exception as exc:  # o erro aparece na interface, sem derrubar o app
                    message = str(exc).strip()
                    op.error = message.splitlines()[-1] if message else type(exc).__name__
            self.mats.push_back(dst, op.title(), space)
