import io
import sys
from typing import List, Dict, Union
import orjson
import click
from pathlib import Path
from zs_parser.tools import fb_parser


def read_ndjson_input(source: Union[str, io.TextIOBase]) -> list[dict]:
    """
    Reads NDJSON from a file path or file-like object using orjson.
    """
    data = []
    if isinstance(source, str):
        f = open(source, 'r', encoding='utf-8')
        should_close = True
    else:  # stdin or file-like
        f = source
        should_close = False

    for line in f:
        stripped_line = line.strip()
        if stripped_line:
            try:
                obj = orjson.loads(stripped_line)
                data.append(obj)
            except orjson.JSONDecodeError as e:
                print(f"[ERROR] Failed to decode line: {stripped_line[:100]}...: {e}")

    if should_close:
        f.close()

    return data

def load_data(input_stream) -> List[Dict]:
    raw = input_stream.read()
    try:
        data = orjson.loads(raw)
        if isinstance(data, list) and all(isinstance(i, dict) for i in data):
            click.echo("Detected JSON array")
            return data
    except orjson.JSONDecodeError:
        pass

    input_stream = io.StringIO(raw)
    click.echo("Detected NDJSON array")
    return read_ndjson_input(input_stream)


@click.command()
@click.argument('input_file', required=False, type=click.File('r', encoding='utf-8'))
def main(input_file):
    """
    Decode Zeeshuimer data to JSON array。

    Usage：
      zs-parser data.ndjson
      zs-parser data.json > out.json
      cat data.ndjson | zs-parser
      head -n 5 data.ndjson | zs-parser
    """
    if input_file:
        input_stream = input_file
    elif not sys.stdin.isatty():
        input_stream = sys.stdin
    else:
        click.echo("Please provide JSON/NDJSON file or pipe in", err=True)
        sys.exit(1)

    try:
        raw_data = load_data(input_stream)
    except Exception as e:
        click.echo(f"Decode failed: {e}", err=True)
        sys.exit(1)

    if not raw_data:
        click.echo("No data in file", err=True)
        return

    parsed_data = fb_parser(raw_data)
    to_file = sys.stdout.isatty()
    output_path = Path("output.json") if to_file else None

    with click.progressbar(length=len(parsed_data)) as bar:
        json_bytes = orjson.dumps(parsed_data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)

        if to_file:
            with output_path.open("wb") as f:
                f.write(json_bytes)
        else:
            sys.stdout.buffer.write(json_bytes)
            sys.stdout.buffer.write(b"\n")

        bar.update(len(parsed_data))

    if to_file:
        click.echo(f"\n✅ Exported JSON to：{output_path}")


if __name__ == "__main__":
    main()
