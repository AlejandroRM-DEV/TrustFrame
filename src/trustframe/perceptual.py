import os
import cv2
from PIL import Image
import imagehash
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from .enums import PerceptualAlgorithm


class PerceptualHasher:
    """
    Handles perceptual hashing of video frames for content-based comparison.

    Perceptual hashes are designed to be similar for visually similar content,
    making them ideal for detecting content modifications while being robust
    to minor compression or format changes.
    """

    AlgorithmFunc = {
        PerceptualAlgorithm.PHASH: imagehash.phash,
        PerceptualAlgorithm.AHASH: imagehash.average_hash,
        PerceptualAlgorithm.DHASH: imagehash.dhash,
        PerceptualAlgorithm.WHASH: imagehash.whash
    }

    def __init__(self, algorithm):
        """
        Initialize the perceptual hasher with a specific algorithm.

        Args:
            algorithm (PerceptualAlgorithm): The perceptual hashing algorithm to use
        """
        self.hash_func = self.AlgorithmFunc[algorithm]
        self.algorithm = algorithm.name

    def get_video_info(self, video_path):
        """
        Extract basic information about a video file.

        Args:
            video_path (str): Path to the video file

        Returns:
            dict: Dictionary containing video metadata
                - total_frames: Total number of frames in the video
                - fps: Frames per second
                - duration_seconds: Video duration in seconds

        Raises:
            FileNotFoundError: If the video file doesn't exist
            ValueError: If the video cannot be opened
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video '{video_path}' does not exist")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video '{video_path}'")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()

        return {
            'total_frames': total_frames,
            'fps': fps,
            'duration_seconds': total_frames / fps if fps > 0 else 0
        }

    def extract_frames(self, video_path, target_frames=None):
        """
        Extract frames from a video file.

        This method can either extract all frames or a specified number of frames
        distributed uniformly throughout the video. Uniform distribution ensures
        that the analysis covers the entire video duration proportionally.

        Args:
            video_path (str): Path to the video file
            target_frames (int, optional): Number of frames to extract. If None,
                                         extracts all frames.

        Returns:
            list: List of dictionaries containing frame data:
                - frame_number: Original frame number in the video
                - extracted_index: Index in the extracted sequence
                - frame_data: RGB numpy array of the frame

        Raises:
            FileNotFoundError: If the video file doesn't exist
            ValueError: If the video cannot be opened
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video '{video_path}' does not exist")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video '{video_path}'")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if target_frames is None:
            # Extract all frames if no target specified
            frames_to_extract = total_frames
            frame_indices = list(range(total_frames))
        else:
            # Distribute target frames uniformly across the video
            frames_to_extract = min(target_frames, total_frames)
            if frames_to_extract == total_frames:
                frame_indices = list(range(total_frames))
            else:
                # Calculate uniformly distributed frame indices
                step = total_frames / frames_to_extract
                frame_indices = [int(i * step) for i in range(frames_to_extract)]

        frames = []

        with Progress(
                TextColumn(f"[bold green]Extracting frames", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Extracting", total=frames_to_extract)

            for i, frame_idx in enumerate(frame_indices):
                # Seek to the specific frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    break

                # Convert from BGR (OpenCV default) to RGB for PIL compatibility
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append({
                    'frame_number': frame_idx + 1,  # 1-based frame numbering
                    'extracted_index': i + 1,  # Index in extraction sequence
                    'frame_data': frame_rgb
                })
                progress.update(task, advance=1)

        cap.release()
        return frames

    def calculate_frame_hashes(self, frames):
        """
        Calculate perceptual hashes for a list of frames.

        Args:
            frames (list): List of frame dictionaries from extract_frames()

        Returns:
            list: List of dictionaries containing hash information:
                - frame_number: Original frame number
                - extracted_index: Index in extraction sequence
                - hash: String representation of the perceptual hash
        """
        hashes = []

        with Progress(
                TextColumn(f"[bold yellow]Calculating {self.algorithm} hashes", justify="right"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Hashing", total=len(frames))

            for frame_info in frames:
                # Convert numpy array to PIL Image for hash calculation
                pil_image = Image.fromarray(frame_info['frame_data'])
                hash_value = self.hash_func(pil_image)
                hashes.append({
                    'frame_number': frame_info['frame_number'],
                    'extracted_index': frame_info['extracted_index'],
                    'hash': str(hash_value)
                })
                progress.update(task, advance=1)

        return hashes

    def analyze_video(self, video_path, target_frames=None):
        """
        Perform complete perceptual analysis of a video file.

        This method combines video information extraction, frame extraction,
        and hash calculation into a single operation.

        Args:
            video_path (str): Path to the video file
            target_frames (int, optional): Number of frames to analyze

        Returns:
            dict: Complete analysis results including:
                - video_path: Path to the analyzed video
                - video_info: Basic video metadata
                - extracted_frames: Number of frames that were analyzed
                - frame_hashes: List of hash data for each frame
        """
        video_info = self.get_video_info(video_path)
        frames = self.extract_frames(video_path, target_frames)
        hashes = self.calculate_frame_hashes(frames)

        return {
            'video_path': video_path,
            'video_info': video_info,
            'extracted_frames': len(frames),
            'frame_hashes': hashes
        }
