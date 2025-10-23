"""Tests for thumbnail service."""

import os
import tempfile
import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import patch, MagicMock

from genonaut.api.services.thumbnail_service import ThumbnailService, ThumbnailSize


class TestThumbnailService:
    """Test cases for thumbnail service."""

    @pytest.fixture
    def thumbnail_service(self):
        """Create thumbnail service instance for testing."""
        with patch('genonaut.api.services.thumbnail_service.get_cached_settings') as mock_cached, \
             patch('genonaut.api.services.thumbnail_service.get_settings') as mock_settings:
            # Mock get_cached_settings to return None so get_settings is used
            mock_cached.return_value = None
            mock_settings.return_value.comfyui_output_dir = "/tmp/test_output"
            service = ThumbnailService()
            # Create temp directories
            Path("/tmp/test_output/thumbnails").mkdir(parents=True, exist_ok=True)
            return service

    @pytest.fixture
    def test_image(self):
        """Create a test image file."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            # Create a simple test image
            img = Image.new('RGB', (800, 600), color='red')
            img.save(temp_file.name, 'PNG')
            yield temp_file.name
            # Cleanup
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_thumbnail_sizes(self):
        """Test that thumbnail sizes are defined correctly."""
        assert ThumbnailSize.SMALL == (150, 150)
        assert ThumbnailSize.MEDIUM == (300, 300)
        assert ThumbnailSize.LARGE == (600, 600)

    def test_thumbnail_service_init(self, thumbnail_service):
        """Test thumbnail service initialization."""
        assert thumbnail_service.settings is not None
        assert thumbnail_service.thumbnail_dir == Path("/tmp/test_output/thumbnails")

    def test_validate_image_valid(self, thumbnail_service, test_image):
        """Test image validation with valid image."""
        assert thumbnail_service.validate_image(test_image) is True

    def test_validate_image_invalid(self, thumbnail_service):
        """Test image validation with invalid file."""
        # Test with non-existent file
        assert thumbnail_service.validate_image("/nonexistent/file.png") is False

        # Test with non-image file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"not an image")
            temp_file.flush()
            try:
                assert thumbnail_service.validate_image(temp_file.name) is False
            finally:
                os.unlink(temp_file.name)

    def test_get_image_info(self, thumbnail_service, test_image):
        """Test getting image information."""
        info = thumbnail_service.get_image_info(test_image)

        assert info is not None
        assert info['width'] == 800
        assert info['height'] == 600
        assert info['mode'] == 'RGB'
        assert info['format'] == 'PNG'
        assert info['file_size'] > 0

    def test_get_image_info_invalid(self, thumbnail_service):
        """Test getting info for invalid image."""
        info = thumbnail_service.get_image_info("/nonexistent/file.png")
        assert info is None

    def test_get_save_kwargs(self, thumbnail_service):
        """Test format-specific save parameters."""
        # Test WebP
        webp_kwargs = thumbnail_service._get_save_kwargs('webp')
        assert webp_kwargs['quality'] == 85
        assert webp_kwargs['method'] == 6
        assert webp_kwargs['optimize'] is True

        # Test JPEG
        jpeg_kwargs = thumbnail_service._get_save_kwargs('jpeg')
        assert jpeg_kwargs['quality'] == 85
        assert jpeg_kwargs['optimize'] is True
        assert jpeg_kwargs['progressive'] is True

        # Test PNG
        png_kwargs = thumbnail_service._get_save_kwargs('png')
        assert png_kwargs['optimize'] is True
        assert png_kwargs['compress_level'] == 6

        # Test unknown format
        unknown_kwargs = thumbnail_service._get_save_kwargs('unknown')
        assert unknown_kwargs == {}

    def test_generate_thumbnails_success(self, thumbnail_service, test_image):
        """Test successful thumbnail generation."""
        # Use temp directory for thumbnails
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnail_service.thumbnail_dir = Path(temp_dir)

            results = thumbnail_service.generate_thumbnails(
                test_image,
                sizes=[(150, 150)],
                formats=['png']
            )

            assert 'png' in results
            assert len(results['png']) == 1

            # Verify thumbnail file exists
            thumbnail_path = results['png'][0]
            assert os.path.exists(thumbnail_path)

            # Verify thumbnail properties
            with Image.open(thumbnail_path) as thumb_img:
                assert thumb_img.width <= 150
                assert thumb_img.height <= 150

    def test_generate_thumbnails_file_not_found(self, thumbnail_service):
        """Test thumbnail generation with non-existent source."""
        with pytest.raises(FileNotFoundError):
            thumbnail_service.generate_thumbnails("/nonexistent/file.png")

    def test_generate_thumbnails_default_params(self, thumbnail_service, test_image):
        """Test thumbnail generation with default parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnail_service.thumbnail_dir = Path(temp_dir)

            results = thumbnail_service.generate_thumbnails(test_image)

            # Should generate default sizes and formats
            assert 'webp' in results
            assert 'png' in results
            assert len(results['webp']) == 3  # 3 default sizes
            assert len(results['png']) == 3

    def test_generate_thumbnail_for_generation(self, thumbnail_service, test_image):
        """Test generation-specific thumbnail creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnail_service.thumbnail_dir = Path(temp_dir)

            results = thumbnail_service.generate_thumbnail_for_generation(
                [test_image],
                generation_id=123
            )

            image_name = Path(test_image).name
            assert image_name in results
            assert 'webp' in results[image_name]
            assert 'png' in results[image_name]

    def test_generate_thumbnail_for_generation_with_error(self, thumbnail_service):
        """Test generation thumbnails with some files failing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            thumbnail_service.thumbnail_dir = Path(temp_dir)

            # Mix of valid and invalid paths
            results = thumbnail_service.generate_thumbnail_for_generation(
                ["/nonexistent/file.png"],
                generation_id=123
            )

            # Should handle errors gracefully
            assert "file.png" in results
            assert results["file.png"] == {'webp': [], 'png': []}

    def test_cleanup_thumbnails(self, thumbnail_service):
        """Test thumbnail cleanup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test thumbnail files
            test_files = []
            for i in range(3):
                test_file = Path(temp_dir) / f"test_thumb_{i}.png"
                test_file.write_text("fake thumbnail")
                test_files.append(str(test_file))

            # Test cleanup
            deleted_count = thumbnail_service.cleanup_thumbnails(test_files)

            assert deleted_count == 3
            for test_file in test_files:
                assert not os.path.exists(test_file)

    def test_cleanup_thumbnails_nonexistent(self, thumbnail_service):
        """Test cleanup with non-existent files."""
        deleted_count = thumbnail_service.cleanup_thumbnails([
            "/nonexistent/file1.png",
            "/nonexistent/file2.png"
        ])

        assert deleted_count == 0

    def test_get_thumbnail_url(self, thumbnail_service):
        """Test thumbnail URL generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a fake thumbnail file
            thumbnail_path = Path(temp_dir) / "test_thumb.png"
            thumbnail_path.write_text("fake thumbnail")

            # Mock the settings to return our temp dir
            with patch.object(thumbnail_service.settings, 'comfyui_output_dir', temp_dir):
                url = thumbnail_service.get_thumbnail_url(str(thumbnail_path))

                expected_relative = thumbnail_path.relative_to(Path(temp_dir))
                assert url == f"/api/v1/images/{expected_relative}"

    def test_get_thumbnail_url_nonexistent(self, thumbnail_service):
        """Test thumbnail URL for non-existent file."""
        url = thumbnail_service.get_thumbnail_url("/nonexistent/file.png")
        assert url is None

    def cleanup_temp_files(self):
        """Clean up any temporary files created during testing."""
        # Remove test output directory if it exists
        test_dir = Path("/tmp/test_output")
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)