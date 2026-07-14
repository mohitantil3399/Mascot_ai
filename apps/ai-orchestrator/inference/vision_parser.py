# inference/vision_parser.py
# 2026 Standard: Region of Interest (ROI) Cropping & Frame Diffing
import io
from PIL import Image, ImageChops
import numpy as np

class VisionPreprocessor:
    def __init__(self, max_dimension: int = 1024, diff_threshold: float = 0.05):
        self.max_dimension = max_dimension
        self.diff_threshold = diff_threshold
        self._last_processed_frame: Image.Image | None = None

    def process_and_check_diff(self, raw_jpeg_bytes: bytes, roi_bounds: tuple[int, int, int, int] | None = None) -> tuple[bytes, bool]:
        """
        Processes incoming JPEG from C# WebSocket:
        1. Crops to Region of Interest (ROI) if specified (x, y, w, h).
        2. Downscales to max_dimension (1024px) using Lanczos while maintaining aspect ratio.
        3. Compares against the last frame to detect if the screen actually changed.
        
        Returns:
            tuple[bytes, bool]: (Processed JPEG bytes, has_significant_change)
        """
        img = Image.open(io.BytesIO(raw_jpeg_bytes)).convert("RGB")

        # 1. Crop to active application bounds if provided
        if roi_bounds:
            x, y, w, h = roi_bounds
            # Ensure bounds are within image limits
            crop_box = (x, y, min(x + w, img.width), min(y + h, img.height))
            if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                img = img.crop(crop_box)

        # 2. Downscale using high-quality Lanczos resampling
        img.thumbnail((self.max_dimension, self.max_dimension), Image.LANCZOS)

        # 3. Check for meaningful visual difference vs previous capture
        has_changed = True
        if self._last_processed_frame is not None and self._last_processed_frame.size == img.size:
            diff = ImageChops.difference(img, self._last_processed_frame)
            diff_arr = np.array(diff)
            # Calculate normalized mean pixel difference across RGB channels
            mean_diff = float(np.mean(diff_arr)) / 255.0
            if mean_diff < self.diff_threshold:
                has_changed = False  # Skip LLM inference — screen is static

        # Update last seen frame cache if significant change occurred
        if has_changed:
            self._last_processed_frame = img.copy()

        # Re-encode optimized frame to JPEG in-memory buffer
        output_buffer = io.BytesIO()
        img.save(output_buffer, format="JPEG", quality=82, optimize=True)
        return output_buffer.getvalue(), has_changed
