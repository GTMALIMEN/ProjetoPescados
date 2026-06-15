# Instalação no Notebook — PostgreSQL + Radar Pescados IA

Este guia é para rodar o projeto em um notebook novo, sem PostgreSQL instalado.

---

## 1. Instalar PostgreSQL no Windows

### Opção recomendada: instalador oficial

1. Baixe o instalador do PostgreSQL para Windows no site oficial.
2. Execute o instalador.
3. Durante a instalação:
   - mantenha a porta `5432`;
   - usuário padrão: `postgres`;
   - senha recomendada para este projeto local: `12345`;
   - instale também o **pgAdmin 4**.

> A senha precisa bater com o arquivo `.env`.

O `.env` deste pacote já está assim:

```env
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=pescadosteste
DB_USER=postgres
DB_PASSWORD=12345
```

Se escolher outra senha no instalador, altere `DB_PASSWORD` no `.env`.

---

## 2. Verificar se o PostgreSQL está rodando

Abra o **pgAdmin 4** ou procure no Windows por:

```text
Services / Serviços
```

Verifique se existe um serviço parecido com:

```text
postgresql-x64-16
postgresql-x64-17
```

e se ele está como **Em execução**.

---

## 3. Preparar o projeto Python

Na pasta do projeto:

```bat
cd "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"
```

Rode:

```bat
scripts\setup_notebook.bat
```

Esse script cria a `.venv` e instala o `requirements.txt`.

Se preferir manualmente:

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Criar o banco e inicializar o projeto

Com a `.venv` ativada:

```bat
python scripts\create_database.py
python scripts\init_db.py
```

Depois rode a primeira carga:

```bat
python scripts\run_bcb_load.py
python scripts\run_ibge_localidades.py
python scripts\run_ibge_populacao.py
python scripts\load_vendas_file.py --arquivo "data\exemplo\vendas_exemplo.csv"
python scripts\calculate_indices_setoriais.py --uf MG --salvar
python scripts\calculate_potencial.py --uf MG --salvar
python scripts\calculate_scores.py --uf MG --salvar
python scripts\generate_recommendations.py --uf MG --salvar
python scripts\generate_active_alerts.py --uf MG --salvar
python scripts\generate_executive_report.py --uf MG --usuario Marcos
python scripts\check_db.py
```

Ou rode tudo com o atalho:

```bat
scripts\primeiro_uso_notebook.bat
```

---

## 5. Abrir o app

```bat
streamlit run app.py
```

Abra no navegador:

```text
http://localhost:8501
```

---

## 6. Erros comuns

### Senha falhou para usuário postgres

A senha do `.env` não é a mesma senha definida no instalador do PostgreSQL.

Corrija:

```env
DB_PASSWORD= sua_senha
```

### Banco não existe

Rode:

```bat
python scripts\create_database.py
```

### Relação/tabela não existe

Rode:

```bat
python scripts\init_db.py
```

### ModuleNotFoundError: No module named 'src'

Você não está rodando da raiz do projeto.

Use:

```bat
cd "C:\Users\ducar\OneDrive\Área de Trabalho\Pescados"
```

### UnicodeEncodeError no Windows

Antes de rodar scripts:

```bat
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
```

---

## 7. Depois do PostgreSQL

Depois que o projeto estiver funcionando localmente, a próxima etapa é subir com Docker.
