# TrustFrame - Video Analysis Tool

TrustFrame is a video analysis tool that compares two video files using both cryptographic and perceptual hashing techniques. It provides detailed analysis of video integrity, frame-by-frame comparison, and sequence alignment to detect modifications, insertions, deletions, and other changes between a reference video and evidence video.

## Features

- **Cryptographic Hash Analysis**: SHA-256, SHA-384, and SHA-512 hashing for file integrity verification
- **Perceptual Hash Analysis**: Multiple perceptual hashing algorithms (pHash, aHash, dHash, wHash) for content comparison
- **Frame-by-frame Comparison**: Detailed analysis of individual video frames
- **Sequence Alignment**: Advanced algorithm to detect insertions, deletions, and substitutions
- **Similarity Scoring**: Hamming distance calculation for precise similarity measurement
- **Progress Tracking**: Real-time progress bars for all operations
- **Rich Output**: Colored tables and formatted reports for easy interpretation

![Help command](/docs/help.png)
![Example part 1](/docs/example-1.png)
![Example part 2](/docs/example-2.png)

## Installation

### Requirements

```bash
pip install opencv-python pillow imagehash typer rich pyfiglet
```

### Dependencies

- **opencv-python**: Video processing and frame extraction
- **pillow**: Image processing
- **imagehash**: Perceptual hashing algorithms
- **typer**: Command-line interface
- **rich**: Enhanced terminal output
- **pyfiglet**: ASCII art banner

## Usage

### Basic Command

```bash
poetry run trustframe  <reference_video> <evidence_video> [OPTIONS]
```

### Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--crypto-algorithm` | Choice | `sha256` | Cryptographic algorithm: `sha256`, `sha384`, `sha512` |
| `--perceptual-algorithm` | Choice | `phash` | Perceptual algorithm: `phash`, `ahash`, `dhash`, `whash` |
| `--max-frames` | Integer | `None` | Maximum frames to analyze (uniform distribution) |

### Examples

**Basic comparison:**
```bash
poetry run trustframe  original.mp4 modified.mp4
```

**Using SHA-512 and dHash with frame limit:**
```bash
poetry run trustframe  original.mp4 modified.mp4 --crypto-algorithm sha512 --perceptual-algorithm dhash --max-frames 1000
```

## Architecture

### Core Classes

#### CryptoHasher
Handles cryptographic hashing of entire video files.

**Supported Algorithms:**
- SHA-256 (default)
- SHA-384
- SHA-512

**Key Methods:**
- `calculate_hash(file_path)`: Computes cryptographic hash with progress tracking

#### PerceptualHasher
Manages perceptual hashing of video frames.

**Supported Algorithms:**
- **pHash** (default): Robust against geometric distortions
- **aHash**: Average hash, fast computation
- **dHash**: Difference hash, good for slight modifications
- **wHash**: Wavelet hash, effective for compression artifacts

**Key Methods:**
- `get_video_info(video_path)`: Extracts video metadata (fps, frame count, duration)
- `extract_frames(video_path, target_frames)`: Extracts frames uniformly or completely
- `calculate_frame_hashes(frames)`: Computes perceptual hashes for frame sequence
- `analyze_video(video_path, target_frames)`: Complete video analysis pipeline

#### VideoComparator
Performs advanced sequence comparison and similarity analysis.

**Key Methods:**
- `calculate_hamming_distance(hash1, hash2)`: Computes bit-level differences and similarity percentage
- `align_sequences(ref_hashes, ev_hashes)`: Dynamic programming algorithm for sequence alignment
- `analyze_differences(alignment)`: Statistical analysis of detected differences

## Analysis Process

### 1. Cryptographic Analysis
- Computes file-level hash for both videos
- Identifies if files are bit-for-bit identical
- Provides binary integrity verification

### 2. Video Information Extraction
- Frame count, FPS, and duration for both videos
- Determines sampling strategy based on `max_frames` parameter

### 3. Frame Extraction
- **Complete Analysis**: Extracts all frames when `max_frames` is not specified
- **Sampled Analysis**: Uniformly distributes specified number of frames across video duration

### 4. Perceptual Hashing
- Applies selected perceptual algorithm to each extracted frame
- Generates hash sequence representing video content

### 5. Sequence Alignment
Uses dynamic programming to find optimal alignment between reference and evidence sequences:

- **Match**: Identical frames in corresponding positions
- **Substitution**: Different frames in corresponding positions
- **Insertion**: Extra frames in evidence video
- **Deletion**: Missing frames from evidence video

### 6. Similarity Calculation
- **Exact Matches**: 100% similarity
- **Substitutions**: Hamming distance-based similarity percentage
- **Insertions/Deletions**: 0% similarity

## Output Format

### Cryptographic Hash Summary
Displays hash values for both videos and binary match status.

### Video Information Table
Shows technical specifications for both input videos.

### Sequence Analysis Summary
Statistical breakdown of operations:
- Match count
- Substitution count
- Insertion count
- Deletion count
- Edit distance (total operations required)

### Detailed Alignment Table
Frame-by-frame comparison showing:
- Operation type
- Reference frame number
- Evidence frame number
- Similarity percentage
- Hash values (first 1000 operations)

### Final Summary Statistics
- Overall average similarity
- Similarity distribution by ranges (high/medium/low)
- Frame modification counts
- Total analyzed frames

## Performance Considerations

### Memory Usage
- Frame data is processed sequentially to minimize memory footprint
- Only frame hashes are retained, not raw image data

### Processing Time
- Cryptographic hashing: Linear with file size
- Frame extraction: Depends on video codec and frame count
- Perceptual hashing: Linear with frame count
- Sequence alignment: O(m×n) where m,n are frame counts

### Optimization Tips
- Use `--max-frames` for large videos to reduce processing time
- Choose appropriate perceptual algorithm based on expected modifications:
  - **pHash**: Best for geometric transformations
  - **dHash**: Optimal for slight content changes
  - **aHash**: Fastest for basic comparisons
  - **wHash**: Effective for compression artifacts

## Algorithm Details

### Sequence Alignment Algorithm
TrustFrame uses the Wagner-Fischer algorithm (edit distance) with traceback to find the optimal alignment between video sequences. This dynamic programming approach efficiently identifies:

1. **Insertions**: Content added to the evidence video
2. **Deletions**: Content removed from the reference video
3. **Substitutions**: Content modified between videos
4. **Matches**: Identical content in both videos

### Hamming Distance Calculation
For perceptual hash comparison, the tool:
1. Converts hexadecimal hashes to binary representation
2. Performs XOR operation to find differing bits
3. Counts set bits in XOR result
4. Calculates similarity as percentage of matching bits

## Error Handling

The tool includes comprehensive error handling for:
- Missing or inaccessible video files
- Corrupt or unsupported video formats
- Insufficient system resources
- Invalid command-line arguments

## Use Cases

### Digital Forensics
- Evidence integrity verification
- Tampering detection
- Timeline reconstruction
- Content authentication

### Media Verification
- Content modification analysis
- Version comparison
- Quality degradation assessment

## Limitations

- **Processing Time**: Large videos require significant computation time
- **Memory Requirements**: High-resolution videos may require substantial RAM
- **Codec Support**: Limited to formats supported by OpenCV
- **Perceptual Accuracy**: Results depend on chosen hashing algorithm and content type

## License

Distributed under the MIT License. See LICENSE file for more information.