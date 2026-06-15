# Radar Pescados IA V2 — Rodar do Zero

## 0. Versão correta do Python

Use **Python 3.12**.

Não use Python 3.14 neste projeto, porque algumas dependências como `pandas` podem não ter wheel pronta e o `pip` tenta compilar do zero.

Para ver suas versões:

```bat
py -0p
```

Se não aparecer Python 3.12, instale o Python 3.12 no Windows e marque:

```text
Add python.exe to PATH
```

Depois feche e abra o CMD novamente.

---

## 1. Instalar PostgreSQL

Durante a instalação:

```text
Porta: 5432
Usuário: postgres
Senha: 12345
pgAdmin: sim
Stack Builder: pode cancelar no final
```

Se usar outra senha, altere o arquivo `.env`.

---

## 2. Entrar na pasta do projeto

Exemplo:

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Nova pasta"
```

---

## 3. Setup Python

```bat
scripts\setup_do_zero.bat
```

Esse script:

```text
verifica se existe Python 3.12
cria .env
cria .env.example
cria .venv com Python 3.12
instala requirements.txt
valida estrutura
```

---

## 4. Se você já criou .venv com Python 3.14

Rode:

```bat
scripts\recriar_venv_python312.bat
```

Ou manualmente:

```bat
rmdir /s /q .venv
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

## 5. Criar banco e carregar bases

```bat
scripts\primeira_execucao_do_zero.bat
```

---

## 6. Abrir app

```bat
scripts\abrir_app.bat
```

Ou:

```bat
.venv\Scripts\activate
streamlit run app.py
```

Acesse:

```text
http://localhost:8501
```

---

## 7. Validar

```bat
scripts\validar_tudo_do_zero.bat
```

---

## 8. Ordem resumida

```bat
cd /d "C:\Users\ducar\OneDrive\Área de Trabalho\Nova pasta"

scripts\setup_do_zero.bat

scripts\primeira_execucao_do_zero.bat

scripts\abrir_app.bat
```

---

## 9. Problemas comuns

### pandas dá erro com Meson / metadata-generation-failed

Você está usando Python 3.14.

Corrija usando Python 3.12:

```bat
scripts\recriar_venv_python312.bat
```

### .env.example ausente

Rode:

```bat
scripts\criar_env_local.bat
```

### Senha falhou para usuário postgres

Corrija no `.env`:

```env
DB_PASSWORD=sua_senha
```

### Banco não existe

```bat
python scripts\create_database.py
```

### Tabela não existe

```bat
python scripts\init_db.py
```

### ModuleNotFoundError: No module named src

Você não está na raiz do projeto. Rode o `cd` correto.
