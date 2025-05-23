import typer
import hashlib
import sys
import os
from enum import Enum
from pathlib import Path
from typing_extensions import Annotated
from rich.progress import Progress, BarColumn, TextColumn, FileSizeColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
from rich import box

app = typer.Typer()


class CryptoAlgorithm(str, Enum):
    SHA256 = 'sha256'
    SHA384 = 'sha384'
    SHA512 = 'sha512'


class PerceptualAlgorithm(str, Enum):
    PHASH = 'phash'


class CryptoHasher:
    CryptoAlgorithmFunc = {
        CryptoAlgorithm.SHA256: hashlib.sha256,
        CryptoAlgorithm.SHA384: hashlib.sha384,
        CryptoAlgorithm.SHA512: hashlib.sha512
    }

    def __init__(self, crypto_algorithm):
        self.hash_func = self.CryptoAlgorithmFunc[crypto_algorithm]

    def calculate_hash(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exists")

        file_size = os.path.getsize(file_path)
        hasher = self.hash_func()

        with open(file_path, "rb") as f:
            with Progress(
                    TextColumn("[bold blue]Processing", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    FileSizeColumn(),
                    "•",
                    TransferSpeedColumn(),
                    "•",
                    TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("Processing", total=file_size)

                for byte_block in iter(lambda: f.read(4096), b""):
                    hasher.update(byte_block)
                    progress.update(task, advance=len(byte_block))

        return hasher.hexdigest()


@app.command()
def analyze(reference: Annotated[Path, typer.Argument(exists=True, file_okay=True, readable=True, resolve_path=True)],
            evidence: Annotated[Path, typer.Argument(exists=True, file_okay=True, readable=True, resolve_path=True)],
            crypto_algorithm: Annotated[CryptoAlgorithm, typer.Option()] = CryptoAlgorithm.SHA256,
            perceptual_algorithm: Annotated[PerceptualAlgorithm, typer.Option()] = PerceptualAlgorithm.PHASH
            ):
    try:
        hasher = CryptoHasher(crypto_algorithm)
        original_hash = hasher.calculate_hash(reference)
        evidence_hash = hasher.calculate_hash(evidence)

        console = Console()

        table = Table(title=f"{crypto_algorithm.name} Hash Summary", box=box.ROUNDED, expand=True)
        table.add_column("File", no_wrap=True)
        value_style = "green" if original_hash == evidence_hash else None
        table.add_column("Value", style=value_style)

        table.add_row("Reference", original_hash)
        table.add_row("Evidence", evidence_hash)

        console.print(table)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    typer.run(analyze)
