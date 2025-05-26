from enum import Enum


class CryptoAlgorithm(str, Enum):
    SHA256 = 'sha256'
    SHA384 = 'sha384'
    SHA512 = 'sha512'


class PerceptualAlgorithm(str, Enum):
    PHASH = 'phash'
    AHASH = 'ahash'
    DHASH = 'dhash'
    WHASH = 'whash'
