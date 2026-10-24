import logging
from pathlib import Path
from typing import Annotated

import typer

from streamstats.analysis import Analyzer
from streamstats.errors import CliConfigError, InvalidEventError, StreamStatsError
from streamstats.parsers import get_parser
from streamstats.report import build_report, write_report

logger = logging.getLogger(__name__)
app = typer.Typer()


@app.callback()
def root():
    logging.basicConfig(level=logging.INFO)

@app.command(name = "analyze")
def analyze(inputs: Annotated[list[Path], typer.Argument()],
            format_files: Annotated[str, typer.Option(..., "--format")],
            output: Annotated[Path | None, typer.Option("--output")] = None,
            skip_invalid: Annotated[bool, typer.Option("--skip-invalid")] = False):

    try:
        parser = get_parser(format_files)
        analyzer = Analyzer()

        for file_path in inputs:
            if not file_path.exists():
                raise CliConfigError(f"Файл не найден: {file_path!s}")
            
            for line_num, result in parser(file_path):
                if isinstance(result, InvalidEventError):
                    if not skip_invalid:
                        raise InvalidEventError(f"{file_path}, строка {line_num}: {result}") from result
                        

                    logger.warning("Skipped invalid row at line %s:%d: %s", file_path, line_num, str(result))
                    analyzer.skip()
                else:
                    analyzer.add(result)

        report = build_report(analyzer)
        write_report(report, output)

    except (StreamStatsError, OSError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2)



if __name__ == "__main__":
    app()


