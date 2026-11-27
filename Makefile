PYTHON ?= python
export SEED ?= 42

.PHONY: data train all

# Prepara o recorte do projeto com os arquivos brutos descritos em docs/fontes-de-dados.md.
data:
	$(PYTHON) src/data/grade.py
	$(PYTHON) src/features/construir_base.py

# O pipeline de treino será implementado em outra tarefa.
train:
	@echo 'Treinamento ainda não implementado (veja T12 e T13).' >&2
	@exit 1

all: data train
