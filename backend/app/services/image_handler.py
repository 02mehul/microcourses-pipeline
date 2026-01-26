import io
import logging
from typing import Dict, List
from ..services.storage import upload_fileobj

logger = logging.getLogger(__name__)


class ImageHandler:
    """
    Handle image processing: download from LlamaParse and upload to MinIO.
    """

    def upload_image_to_minio(
        self, image_data: bytes, document_id: int, page_num: int, index: int, ext: str = "jpg"
    ) -> str:
        """
        Upload image to MinIO and return the storage path.
        
        Args:
            image_data: Image bytes
            document_id: Document ID
            page_num: Page number
            index: Image index on the page
            ext: File extension
            
        Returns:
            MinIO storage path
        """
        # Create organized path: images/{document_id}/{page_num}_{index}.{ext}
        path = f"images/{document_id}/page_{page_num}_img_{index}.{ext}"
        
        try:
            # Upload to MinIO
            upload_fileobj(io.BytesIO(image_data), path)
            logger.info(f"Uploaded image to MinIO: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to upload image to MinIO: {e}", exc_info=True)
            raise

    def process_llamaparse_images(
        self, images: List[Dict], document_id: int
    ) -> Dict[str, str]:
        """
        Process LlamaParse images and upload to MinIO.
        
        Args:
            images: List of image info dicts from LlamaParse
            document_id: Document ID
            
        Returns:
            Mapping of image names to MinIO paths
        """
        image_paths = {}
        
        for img_info in images:
            try:
                # Extract image details
                name = img_info.get("name", "")
                # Image data might be in 'bytes' or we need to download from URL
                image_bytes = img_info.get("bytes")
                
                if not image_bytes:
                    # Skip if no image data
                    logger.warning(f"No image data for {name}")
                    continue
                
                # Parse page number and index from name (e.g., "page_1_image_0.jpg")
                # This depends on LlamaParse's naming convention
                parts = name.split("_")
                try:
                    page_num = int(parts[1]) if len(parts) > 1 else 1
                    index = int(parts[3].split(".")[0]) if len(parts) > 3 else 0
                except (ValueError, IndexError):
                    page_num = 1
                    index = 0
                
                # Determine extension
                ext = name.split(".")[-1] if "." in name else "jpg"
                
                # Upload to MinIO
                minio_path = self.upload_image_to_minio(
                    image_bytes, document_id, page_num, index, ext
                )
                
                image_paths[name] = minio_path
                
            except Exception as e:
                logger.error(f"Error processing image {img_info}: {e}", exc_info=True)
                continue
        
        return image_paths
