from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import text
from src.database.connection import get_engine


def main():
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM app.fato_cepea_tilapia_manual"))
        conn.execute(text("""
            DELETE FROM dw.fato_indicador_setorial
            WHERE fonte = 'CEPEA'
              AND subcategoria = 'oficial_arquivo_manual'
        """))
        conn.execute(text("""
            UPDATE dw.fato_indicador_setorial
            SET fonte = 'CEPEA_MANUAL_IMPORTADO',
                subcategoria = 'proxy_antigo'
            WHERE fonte = 'CEPEA'
              AND subcategoria NOT IN ('oficial_site_produtor_independente')
              AND indicador ILIKE '%cepea%'
        """))
    print('CEPEA manual antigo limpo. Agora importe o modelo novo usando substituir_tudo.')


if __name__ == '__main__':
    main()
