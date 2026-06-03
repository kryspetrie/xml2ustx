import sys

from src.application.Xml2UstxRunner import run_cli

if __name__ == '__main__':
    try:
        run_cli()
    except Exception as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


