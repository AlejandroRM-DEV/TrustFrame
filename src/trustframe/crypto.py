import os
import hashlib
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from .enums import CryptoAlgorithm


class CryptoHasher:
    """
    Handles cryptographic hashing of files for integrity verification.

    This class provides functionality to calculate cryptographic hashes
    of entire files, which can detect any binary-level modifications.
    """

    AlgorithmFunc = {
        CryptoAlgorithm.SHA256: hashlib.sha256,
        CryptoAlgorithm.SHA384: hashlib.sha384,
        CryptoAlgorithm.SHA512: hashlib.sha512
    }

    def __init__(self, algorithm):
        """
        Initialize the hasher with a specific algorithm.

        Args:
            algorithm (CryptoAlgorithm): The cryptographic algorithm to use
        """
        self.hash_func = self.AlgorithmFunc[algorithm]
        self.algorithm = algorithm.name

    def calculate_hash(self, file_path):
        """
        Calculate the cryptographic hash of a file.

        This method reads the file in chunks to handle large files efficiently
        while providing progress feedback to the user.

        Args:
            file_path (str): Path to the file to hash

        Returns:
            str: Hexadecimal representation of the hash

        Raises:
            FileNotFoundError: If the specified file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' does not exists")

        file_size = os.path.getsize(file_path)
        hasher = self.hash_func()

        # Read file in 4KB chunks to manage memory usage
        with open(file_path, "rb") as f:
            with Progress(
                    TextColumn(f"[bold green]Calculating {self.algorithm} hash", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task("Processing", total=file_size)

                # Process file in chunks
                for byte_block in iter(lambda: f.read(4096), b""):
                    hasher.update(byte_block)
                    progress.update(task, advance=len(byte_block))

        return hasher.hexdigest()
