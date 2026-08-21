import argparse
import json
from pathlib import Path

from app.incident import analyze_logs


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify deployment and system logs")
    parser.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(analyze_logs(args.file.read_text(encoding="utf-8", errors="replace")), indent=2)
    )


if __name__ == "__main__":
    main()
