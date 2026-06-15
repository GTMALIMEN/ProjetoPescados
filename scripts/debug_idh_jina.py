from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.collectors.atlas_brasil_collector import AtlasBrasilCollector


def main():
    collector = AtlasBrasilCollector()
    df, meta = collector._try_url(collector.jina_undp_url)

    print("Status HTTP:", meta.get("status_http"))
    print("Content-Type:", meta.get("content_type"))
    print("Qtd registros parseados:", len(df))
    print("Debug file:", meta.get("debug_file"))
    print("Preview:")
    print((meta.get("preview") or "")[:2000])

    if not df.empty:
        print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
