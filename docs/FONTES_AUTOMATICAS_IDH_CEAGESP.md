# Fontes automáticas — IDH/IDHM e CEAGESP

IDH/IDHM municipal e CEAGESP deixam de ser importadores manuais.

```bat
python scripts\apply_fontes_automaticas.py
python scripts\run_idh_automatico.py
python scripts\run_ceagesp_automatico.py --dias-busca 21
python scripts\diagnosticar_v2_plano.py
```

Ou rode `scripts\rodar_fontes_automaticas.bat`.

O IDH/IDHM usa Atlas Brasil/PNUD/dados.gov.br quando o link público estiver acessível. O CEAGESP usa descoberta do formulário oficial de cotações por produto/data.
