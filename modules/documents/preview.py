"""
Document Preview Generation Module

Provides comprehensive document preview and thumbnail generation capabilities
for various document formats.

Features:
- Multi-format preview support
- Thumbnail generation with customizable sizes
- Image optimization
- PDF preview generation
- Office document preview
- Caching support
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import json

logger = logging.getLogger(__name__)


class PreviewSize(Enum):
    """Standard preview sizes."""
    THUMBNAIL = (150, 150)
    SMALL = (300, 300)
    MEDIUM = (600, 600)
    LARGE = (1200, 1200)
    CUSTOM = None


class PreviewFormat(Enum):
    """Preview output formats."""
    PNG = "png"
    JPEG = "jpg"
    WEBP = "webp"


class PreviewError(Exception):
    """Base exception for preview generation errors."""
    pass


class PreviewConfig:
    """Configuration for preview generation."""

    def __init__(
        self,
        size: Union[PreviewSize, Tuple[int, int]] = PreviewSize.MEDIUM,
        format: PreviewFormat = PreviewFormat.PNG,
        quality: int = 85,
        maintain_aspect_ratio: bool = True,
        cache_enabled: bool = True,
        cache_ttl: int = 86400,  # 24 hours
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ):
        """
        Initialize preview configuration.

        Args:
            size: Preview size (PreviewSize enum or custom tuple)
            format: Output format
            quality: Image quality (1-100)
            maintain_aspect_ratio: Whether to maintain aspect ratio
            cache_enabled: Enable preview caching
            cache_ttl: Cache time-to-live in seconds
            background_color: Background color for transparent images (RGB)
        """
        self.size = size.value if isinstance(size, PreviewSize) else size
        self.format = format
        self.quality = max(1, min(100, quality))
        self.maintain_aspect_ratio = maintain_aspect_ratio
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.background_color = background_color


class PreviewGenerator:
    """
    Main preview generation class for various document types.

    Generates previews and thumbnails for:
    - Images
    - PDF documents
    - Office documents
    - Text files
    - Other supported formats
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        libreoffice_path: Optional[str] = None,
        imagemagick_path: Optional[str] = None
    ):
        """
        Initialize preview generator.

        Args:
            cache_dir: Directory for caching previews
            temp_dir: Temporary directory for processing
            libreoffice_path: Path to LibreOffice executable
            imagemagick_path: Path to ImageMagick convert executable
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(tempfile.gettempdir()) / "preview_cache"
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self.libreoffice_path = libreoffice_path or "libreoffice"
        self.imagemagick_path = imagemagick_path or "convert"

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"PreviewGenerator initialized with cache: {self.cache_dir}")

    def generate_preview(
        self,
        file_path: Union[str, Path],
        config: Optional[PreviewConfig] = None,
        page: int = 1
    ) -> Path:
        """
        Generate a preview for a document.

        Args:
            file_path: Path to the document
            config: Preview configuration (uses defaults if not provided)
            page: Page number for multi-page documents (1-indexed)

        Returns:
            Path to generated preview image

        Raises:
            PreviewError: If preview generation fails
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        config = config or PreviewConfig()

        # Check cache
        if config.cache_enabled:
            cache_key = self._generate_cache_key(file_path, config, page)
            cached_preview = self._get_cached_preview(cache_key, config.cache_ttl)

            if cached_preview:
                logger.info(f"Using cached preview for {file_path.name}")
                return cached_preview

        logger.info(f"Generating preview for {file_path.name}")

        try:
            # Determine file type and generate preview
            extension = file_path.suffix.lower()

            if extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']:
                preview_path = self._generate_image_preview(file_path, config)
            elif extension == '.pdf':
                preview_path = self._generate_pdf_preview(file_path, config, page)
            elif extension in ['.docx', '.doc', '.odt', '.rtf']:
                preview_path = self._generate_office_preview(file_path, config, page)
            elif extension in ['.xlsx', '.xls', '.ods']:
                preview_path = self._generate_spreadsheet_preview(file_path, config)
            elif extension in ['.pptx', '.ppt', '.odp']:
                preview_path = self._generate_presentation_preview(file_path, config, page)
            elif extension in ['.txt', '.md', '.csv']:
                preview_path = self._generate_text_preview(file_path, config)
            else:
                preview_path = self._generate_generic_preview(file_path, config)

            # Cache the preview
            if config.cache_enabled:
                self._cache_preview(preview_path, cache_key)

            return preview_path

        except Exception as e:
            logger.error(f"Preview generation failed: {e}", exc_info=True)
            raise PreviewError(f"Failed to generate preview: {e}") from e

    def generate_thumbnail(
        self,
        file_path: Union[str, Path],
        size: Union[PreviewSize, Tuple[int, int]] = PreviewSize.THUMBNAIL
    ) -> Path:
        """
        Generate a thumbnail for a document.

        Args:
            file_path: Path to the document
            size: Thumbnail size

        Returns:
            Path to generated thumbnail
        """
        config = PreviewConfig(
            size=size,
            format=PreviewFormat.JPEG,
            quality=80,
            maintain_aspect_ratio=True
        )

        return self.generate_preview(file_path, config)

    def _generate_image_preview(
        self,
        file_path: Path,
        config: PreviewConfig
    ) -> Path:
        """Generate preview for image files."""
        try:
            from PIL import Image, ImageOps

            output_path = self._get_output_path(file_path, config)

            with Image.open(file_path) as img:
                # Handle orientation
                img = ImageOps.exif_transpose(img)

                # Convert RGBA to RGB if saving as JPEG
                if config.format == PreviewFormat.JPEG and img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, config.background_color)
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    img = background

                # Resize image
                if config.size:
                    if config.maintain_aspect_ratio:
                        img.thumbnail(config.size, Image.Resampling.LANCZOS)
                    else:
                        img = img.resize(config.size, Image.Resampling.LANCZOS)

                # Save with optimization
                save_kwargs = {}
                if config.format == PreviewFormat.JPEG:
                    save_kwargs['quality'] = config.quality
                    save_kwargs['optimize'] = True
                elif config.format == PreviewFormat.PNG:
                    save_kwargs['optimize'] = True
                elif config.format == PreviewFormat.WEBP:
                    save_kwargs['quality'] = config.quality

                img.save(output_path, format=config.format.value.upper(), **save_kwargs)

            logger.info(f"Image preview generated: {output_path}")
            return output_path

        except ImportError:
            raise PreviewError("Pillow library required for image preview generation")
        except Exception as e:
            raise PreviewError(f"Image preview generation failed: {e}")

    def _generate_pdf_preview(
        self,
        file_path: Path,
        config: PreviewConfig,
        page: int
    ) -> Path:
        """Generate preview for PDF files."""
        try:
            import fitz  # PyMuPDF

            output_path = self._get_output_path(file_path, config)

            with fitz.open(file_path) as doc:
                if page > len(doc):
                    page = 1

                # Get the specified page (0-indexed)
                pdf_page = doc[page - 1]

                # Calculate zoom factor to achieve desired size
                if config.size:
                    rect = pdf_page.rect
                    zoom_x = config.size[0] / rect.width
                    zoom_y = config.size[1] / rect.height

                    if config.maintain_aspect_ratio:
                        zoom = min(zoom_x, zoom_y)
                        matrix = fitz.Matrix(zoom, zoom)
                    else:
                        matrix = fitz.Matrix(zoom_x, zoom_y)
                else:
                    matrix = fitz.Matrix(2, 2)  # Default 2x zoom

                # Render page to image
                pix = pdf_page.get_pixmap(matrix=matrix)

                # Convert to PIL Image for further processing
                from PIL import Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Save preview
                save_kwargs = {}
                if config.format == PreviewFormat.JPEG:
                    save_kwargs['quality'] = config.quality
                    save_kwargs['optimize'] = True
                elif config.format == PreviewFormat.PNG:
                    save_kwargs['optimize'] = True

                img.save(output_path, format=config.format.value.upper(), **save_kwargs)

            logger.info(f"PDF preview generated: {output_path}")
            return output_path

        except ImportError:
            logger.warning("PyMuPDF not available, trying fallback method")
            return self._generate_pdf_preview_fallback(file_path, config, page)
        except Exception as e:
            raise PreviewError(f"PDF preview generation failed: {e}")

    def _generate_pdf_preview_fallback(
        self,
        file_path: Path,
        config: PreviewConfig,
        page: int
    ) -> Path:
        """Fallback PDF preview using ImageMagick."""
        try:
            output_path = self._get_output_path(file_path, config)

            cmd = [
                self.imagemagick_path,
                "-density", "150",
                f"{file_path}[{page - 1}]",  # Specify page (0-indexed)
                "-quality", str(config.quality),
                "-flatten",
                "-background", f"rgb{config.background_color}"
            ]

            if config.size:
                size_str = f"{config.size[0]}x{config.size[1]}"
                if config.maintain_aspect_ratio:
                    cmd.extend(["-thumbnail", size_str])
                else:
                    cmd.extend(["-resize", size_str + "!"])

            cmd.append(str(output_path))

            subprocess.run(cmd, capture_output=True, check=True, timeout=60)

            return output_path

        except subprocess.CalledProcessError as e:
            raise PreviewError(f"ImageMagick PDF conversion failed: {e.stderr}")
        except FileNotFoundError:
            raise PreviewError("ImageMagick not available for PDF preview generation")

    def _generate_office_preview(
        self,
        file_path: Path,
        config: PreviewConfig,
        page: int
    ) -> Path:
        """Generate preview for office documents."""
        # First convert to PDF, then generate preview from PDF
        try:
            temp_pdf = self.temp_dir / f"{file_path.stem}_temp.pdf"

            # Convert to PDF using LibreOffice
            cmd = [
                self.libreoffice_path,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(self.temp_dir),
                str(file_path)
            ]

            subprocess.run(cmd, capture_output=True, check=True, timeout=120)

            # Generate preview from the PDF
            preview_path = self._generate_pdf_preview(temp_pdf, config, page)

            # Clean up temporary PDF
            temp_pdf.unlink(missing_ok=True)

            return preview_path

        except subprocess.CalledProcessError as e:
            raise PreviewError(f"Office document conversion failed: {e.stderr}")
        except Exception as e:
            raise PreviewError(f"Office preview generation failed: {e}")

    def _generate_spreadsheet_preview(
        self,
        file_path: Path,
        config: PreviewConfig
    ) -> Path:
        """Generate preview for spreadsheet files."""
        # Use office preview generation (convert to PDF first)
        return self._generate_office_preview(file_path, config, 1)

    def _generate_presentation_preview(
        self,
        file_path: Path,
        config: PreviewConfig,
        page: int
    ) -> Path:
        """Generate preview for presentation files."""
        # Use office preview generation (convert to PDF first)
        return self._generate_office_preview(file_path, config, page)

    def _generate_text_preview(
        self,
        file_path: Path,
        config: PreviewConfig
    ) -> Path:
        """Generate preview for text files."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            output_path = self._get_output_path(file_path, config)

            # Read first few lines of text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline().rstrip() for _ in range(30)]

            # Create image
            width, height = config.size or (800, 600)
            img = Image.new('RGB', (width, height), config.background_color)
            draw = ImageDraw.Draw(img)

            # Try to use a monospace font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
            except:
                font = ImageFont.load_default()

            # Draw text
            y_offset = 10
            for line in lines:
                if y_offset > height - 20:
                    break
                draw.text((10, y_offset), line[:100], fill=(0, 0, 0), font=font)
                y_offset += 20

            # Save preview
            save_kwargs = {'quality': config.quality} if config.format == PreviewFormat.JPEG else {}
            img.save(output_path, format=config.format.value.upper(), **save_kwargs)

            return output_path

        except ImportError:
            raise PreviewError("Pillow library required for text preview generation")
        except Exception as e:
            raise PreviewError(f"Text preview generation failed: {e}")

    def _generate_generic_preview(
        self,
        file_path: Path,
        config: PreviewConfig
    ) -> Path:
        """Generate a generic preview icon for unsupported formats."""
        try:
            from PIL import Image, ImageDraw, ImageFont

            output_path = self._get_output_path(file_path, config)

            # Create image with file type
            width, height = config.size or (400, 400)
            img = Image.new('RGB', (width, height), (240, 240, 240))
            draw = ImageDraw.Draw(img)

            # Draw border
            draw.rectangle(
                [(10, 10), (width - 10, height - 10)],
                outline=(100, 100, 100),
                width=2
            )

            # Draw file extension
            ext = file_path.suffix.upper()
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()

            text_bbox = draw.textbbox((0, 0), ext, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) // 2
            text_y = (height - text_height) // 2

            draw.text((text_x, text_y), ext, fill=(100, 100, 100), font=font)

            # Save preview
            save_kwargs = {'quality': config.quality} if config.format == PreviewFormat.JPEG else {}
            img.save(output_path, format=config.format.value.upper(), **save_kwargs)

            return output_path

        except ImportError:
            raise PreviewError("Pillow library required for generic preview generation")

    def _get_output_path(self, file_path: Path, config: PreviewConfig) -> Path:
        """Generate output path for preview."""
        ext = config.format.value
        return self.temp_dir / f"{file_path.stem}_preview.{ext}"

    def _generate_cache_key(
        self,
        file_path: Path,
        config: PreviewConfig,
        page: int
    ) -> str:
        """Generate cache key for a preview."""
        # Include file path, modification time, config, and page
        mtime = file_path.stat().st_mtime
        cache_data = f"{file_path}:{mtime}:{config.size}:{config.format.value}:{config.quality}:{page}"

        return hashlib.sha256(cache_data.encode()).hexdigest()

    def _get_cached_preview(self, cache_key: str, ttl: int) -> Optional[Path]:
        """Retrieve cached preview if available and not expired."""
        cache_file = self.cache_dir / cache_key
        metadata_file = self.cache_dir / f"{cache_key}.meta"

        if not cache_file.exists() or not metadata_file.exists():
            return None

        try:
            # Check if cache is expired
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            created_at = datetime.fromisoformat(metadata['created_at'])
            if datetime.now() - created_at > timedelta(seconds=ttl):
                logger.debug(f"Cache expired for {cache_key}")
                cache_file.unlink(missing_ok=True)
                metadata_file.unlink(missing_ok=True)
                return None

            logger.info(f"Cache hit for {cache_key}")
            return cache_file

        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None

    def _cache_preview(self, preview_path: Path, cache_key: str) -> None:
        """Cache a generated preview."""
        try:
            import shutil

            cache_file = self.cache_dir / cache_key
            metadata_file = self.cache_dir / f"{cache_key}.meta"

            # Copy preview to cache
            shutil.copy2(preview_path, cache_file)

            # Write metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'original_path': str(preview_path)
            }

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

            logger.debug(f"Preview cached with key: {cache_key}")

        except Exception as e:
            logger.warning(f"Failed to cache preview: {e}")

    def clear_cache(self, older_than: Optional[int] = None) -> int:
        """
        Clear the preview cache.

        Args:
            older_than: Only clear cache files older than this many seconds

        Returns:
            Number of files removed
        """
        removed = 0

        try:
            for cache_file in self.cache_dir.iterdir():
                if cache_file.suffix == '.meta':
                    continue

                should_remove = False

                if older_than is None:
                    should_remove = True
                else:
                    file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
                    if file_age > older_than:
                        should_remove = True

                if should_remove:
                    cache_file.unlink(missing_ok=True)
                    metadata_file = self.cache_dir / f"{cache_file.name}.meta"
                    metadata_file.unlink(missing_ok=True)
                    removed += 1

            logger.info(f"Cleared {removed} cached previews")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

        return removed


class ImageOptimizer:
    """
    Image optimization utilities for reducing file size while maintaining quality.
    """

    def __init__(self):
        """Initialize image optimizer."""
        logger.info("ImageOptimizer initialized")

    def optimize(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        quality: int = 85,
        max_size: Optional[Tuple[int, int]] = None,
        format: Optional[str] = None
    ) -> Path:
        """
        Optimize an image file.

        Args:
            image_path: Path to input image
            output_path: Path for optimized image (overwrites input if not provided)
            quality: JPEG quality (1-100)
            max_size: Maximum dimensions (width, height)
            format: Output format (auto-detect if not provided)

        Returns:
            Path to optimized image

        Raises:
            PreviewError: If optimization fails
        """
        try:
            from PIL import Image

            image_path = Path(image_path)
            output_path = Path(output_path) if output_path else image_path

            with Image.open(image_path) as img:
                # Resize if max_size is specified
                if max_size and (img.width > max_size[0] or img.height > max_size[1]):
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized image to {img.size}")

                # Determine output format
                if format:
                    save_format = format.upper()
                else:
                    save_format = img.format or 'JPEG'

                # Optimize and save
                save_kwargs = {'optimize': True}

                if save_format in ['JPEG', 'JPG']:
                    save_kwargs['quality'] = quality
                    # Convert RGBA to RGB for JPEG
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        if img.mode in ('RGBA', 'LA'):
                            background.paste(img, mask=img.split()[-1])
                        img = background

                img.save(output_path, format=save_format, **save_kwargs)

            logger.info(f"Image optimized: {output_path}")
            return output_path

        except ImportError:
            raise PreviewError("Pillow library required for image optimization")
        except Exception as e:
            raise PreviewError(f"Image optimization failed: {e}")


# Convenience functions
def generate_preview(
    file_path: Union[str, Path],
    size: Union[PreviewSize, Tuple[int, int]] = PreviewSize.MEDIUM,
    format: PreviewFormat = PreviewFormat.PNG,
    page: int = 1
) -> Path:
    """
    Convenience function to generate a document preview.

    Args:
        file_path: Path to document
        size: Preview size
        format: Output format
        page: Page number for multi-page documents

    Returns:
        Path to generated preview
    """
    generator = PreviewGenerator()
    config = PreviewConfig(size=size, format=format)
    return generator.generate_preview(file_path, config, page)


def generate_thumbnail(
    file_path: Union[str, Path],
    size: Union[PreviewSize, Tuple[int, int]] = PreviewSize.THUMBNAIL
) -> Path:
    """
    Convenience function to generate a thumbnail.

    Args:
        file_path: Path to document
        size: Thumbnail size

    Returns:
        Path to generated thumbnail
    """
    generator = PreviewGenerator()
    return generator.generate_thumbnail(file_path, size)


def optimize_image(
    image_path: Union[str, Path],
    quality: int = 85,
    max_size: Optional[Tuple[int, int]] = None
) -> Path:
    """
    Convenience function to optimize an image.

    Args:
        image_path: Path to image
        quality: JPEG quality
        max_size: Maximum dimensions

    Returns:
        Path to optimized image
    """
    optimizer = ImageOptimizer()
    return optimizer.optimize(image_path, quality=quality, max_size=max_size)
