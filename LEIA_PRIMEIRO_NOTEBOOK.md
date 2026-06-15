# LEIA PRIMEIRO — Notebook novo

Você está em um notebook sem PostgreSQL instalado.

## Ordem correta

1. Instalar PostgreSQL no Windows.
2. Usar senha `12345` no usuário `postgres`, ou alterar o `.env`.
3. Rodar setup Python:

```bat
scripts\setup_notebook.bat
```

4. Criar banco e inicializar:

```bat
python scripts\create_database.py
python scripts\init_db.py
```

5. Rodar primeira carga completa:

```bat
scripts\primeiro_uso_notebook.bat
```

6. Abrir app:

```bat
streamlit run app.py
```

Documentação completa:

```text
docs/INSTALACAO_NOTEBOOK_POSTGRES.md
```


## Recarregar todas as fontes 2020–2026

```bat
scripts\recarregar_fontes_2020_2026.bat
```

Esse comando corrige:
- Região Comercial MG;
- Proteínas de 2020 até 2026;
- Grãos/insumos de 2020 até 2026;
- Comex Stat de 2020 até 2026.
