"""OCR service for processing receipt images."""

import io
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from PIL import Image
import pytesseract
import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.expense import ExpenseAttachment

logger = logging.getLogger(__name__)


class OCRService:
    """Service for processing receipt images with OCR."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def process_receipt_image(self, attachment_id: int) -> Dict:
        """Process receipt image and extract text using OCR."""
        
        attachment = self.db.query(ExpenseAttachment).filter(
            ExpenseAttachment.id == attachment_id
        ).first()
        
        if not attachment:
            raise ValueError("Attachment not found")
        
        try:
            # Load and preprocess image
            image = self._load_and_preprocess_image(attachment.file_path)
            
            # Perform OCR
            ocr_result = self._perform_ocr(image)
            
            # Extract structured data
            structured_data = self._extract_structured_data(ocr_result['text'])
            
            # Update attachment with OCR results
            attachment.ocr_text = ocr_result['text']
            attachment.ocr_confidence = Decimal(str(ocr_result['confidence']))
            attachment.ocr_language = ocr_result['language']
            attachment.is_processed = True
            attachment.processing_status = "completed"
            
            self.db.commit()
            
            result = {
                "success": True,
                "text": ocr_result['text'],
                "confidence": ocr_result['confidence'],
                "language": ocr_result['language'],
                "structured_data": structured_data
            }
            
            logger.info(f"Successfully processed OCR for attachment {attachment_id}")
            return result
            
        except Exception as e:
            # Update processing status on failure
            attachment.processing_status = "failed"
            self.db.commit()
            
            logger.error(f"OCR processing failed for attachment {attachment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _load_and_preprocess_image(self, file_path: str) -> np.ndarray:
        """Load and preprocess image for better OCR results."""
        
        # Load image using OpenCV
        image = cv2.imread(file_path)
        
        if image is None:
            raise ValueError("Could not load image file")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply noise reduction
        denoised = cv2.medianBlur(gray, 3)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Deskew image if needed
        deskewed = self._deskew_image(thresh)
        
        # Resize image for better OCR (if too small)
        height, width = deskewed.shape
        if height < 600:
            scale_factor = 600 / height
            new_width = int(width * scale_factor)
            deskewed = cv2.resize(deskewed, (new_width, 600), interpolation=cv2.INTER_CUBIC)
        
        return deskewed
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image to correct rotation."""
        
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Only deskew if angle is significant
        if abs(angle) > 0.5:
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
            return rotated
        
        return image
    
    def _perform_ocr(self, image: np.ndarray) -> Dict:
        """Perform OCR on preprocessed image."""
        
        # Configure Tesseract for Chinese and English
        config = r'--oem 3 --psm 6 -l chi_sim+chi_tra+eng'
        
        try:
            # Get text with confidence scores
            data = pytesseract.image_to_data(
                image, config=config, output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text_parts = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                confidence = int(data['conf'][i])
                if confidence > 30 and word.strip():  # Filter low confidence words
                    text_parts.append(word)
                    confidences.append(confidence)
            
            text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Detect language
            language = self._detect_language(text)
            
            return {
                "text": text,
                "confidence": avg_confidence,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise
    
    def _detect_language(self, text: str) -> str:
        """Detect primary language of the text."""
        
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "zh"
        else:
            return "en"
    
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract structured data from OCR text."""
        
        structured_data = {
            "vendor": None,
            "amount": None,
            "currency": None,
            "date": None,
            "tax_amount": None,
            "items": []
        }
        
        # Extract amount patterns
        amounts = self._extract_amounts(text)
        if amounts:
            structured_data["amount"] = amounts[0]["amount"]
            structured_data["currency"] = amounts[0]["currency"]
        
        # Extract vendor/store name
        vendor = self._extract_vendor_name(text)
        if vendor:
            structured_data["vendor"] = vendor
        
        # Extract date
        date = self._extract_date(text)
        if date:
            structured_data["date"] = date
        
        # Extract tax information
        tax_amount = self._extract_tax_amount(text)
        if tax_amount:
            structured_data["tax_amount"] = tax_amount
        
        return structured_data
    
    def _extract_amounts(self, text: str) -> list:
        """Extract monetary amounts from text."""
        import re
        
        amounts = []
        
        # Patterns for different currencies
        patterns = [
            # HKD patterns
            (r'HK\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'HKD'),
            (r'港幣\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'HKD'),
            (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*HKD', 'HKD'),
            
            # USD patterns
            (r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
            (r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'USD'),
            (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*USD', 'USD'),
            
            # RMB patterns
            (r'¥\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'RMB'),
            (r'RMB\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'RMB'),
            (r'人民币\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'RMB'),
            (r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*元', 'RMB'),
            
            # EUR patterns
            (r'€\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
            (r'EUR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', 'EUR'),
            
            # JPY patterns
            (r'¥\s*(\d+(?:,\d{3})*)', 'JPY'),
            (r'JPY\s*(\d+(?:,\d{3})*)', 'JPY'),
            (r'(\d+(?:,\d{3})*)\s*円', 'JPY'),
        ]
        
        for pattern, currency in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = Decimal(amount_str)
                    amounts.append({
                        "amount": amount,
                        "currency": currency,
                        "confidence": 0.8  # Base confidence
                    })
                except:
                    continue
        
        # Sort by amount (largest first, likely to be total)
        amounts.sort(key=lambda x: x["amount"], reverse=True)
        
        return amounts
    
    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor/store name from receipt."""
        
        lines = text.split('\n')
        
        # Usually vendor name is in the first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if len(line) > 3 and not line.isdigit():
                # Skip common receipt headers
                skip_patterns = ['receipt', 'invoice', 'bill', '收据', '发票', '账单']
                if not any(pattern in line.lower() for pattern in skip_patterns):
                    return line
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt text."""
        import re
        
        # Date patterns
        date_patterns = [
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # DD-MM-YYYY or MM/DD/YYYY
            r'(\d{4}年\d{1,2}月\d{1,2}日)',     # Chinese date format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_tax_amount(self, text: str) -> Optional[Decimal]:
        """Extract tax amount from receipt."""
        import re
        
        # Tax patterns
        tax_patterns = [
            r'税[额金]\s*[:：]\s*(\d+(?:\.\d{2})?)',
            r'TAX\s*[:：]\s*(\d+(?:\.\d{2})?)',
            r'GST\s*[:：]\s*(\d+(?:\.\d{2})?)',
            r'VAT\s*[:：]\s*(\d+(?:\.\d{2})?)',
        ]
        
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    continue
        
        return None
    
    def create_thumbnail(self, attachment_id: int, max_size: Tuple[int, int] = (300, 300)) -> bool:
        """Create thumbnail for image attachment."""
        
        attachment = self.db.query(ExpenseAttachment).filter(
            ExpenseAttachment.id == attachment_id
        ).first()
        
        if not attachment:
            return False
        
        try:
            # Load original image
            with Image.open(attachment.file_path) as img:
                # Create thumbnail
                img.thumbnail(max_size, Image.LANCZOS)
                
                # Save thumbnail
                thumbnail_path = attachment.file_path.replace('.', '_thumb.')
                img.save(thumbnail_path, quality=85, optimize=True)
                
                # Update attachment record
                attachment.thumbnail_path = thumbnail_path
                self.db.commit()
                
                logger.info(f"Created thumbnail for attachment {attachment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create thumbnail for attachment {attachment_id}: {e}")
            return False
    
    def compress_image(self, attachment_id: int, quality: int = 85) -> bool:
        """Compress image to reduce file size."""
        
        attachment = self.db.query(ExpenseAttachment).filter(
            ExpenseAttachment.id == attachment_id
        ).first()
        
        if not attachment:
            return False
        
        try:
            # Load original image
            with Image.open(attachment.file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Save compressed version
                compressed_path = attachment.file_path.replace('.', '_compressed.')
                img.save(compressed_path, "JPEG", quality=quality, optimize=True)
                
                # Get compressed file size
                import os
                compressed_size = os.path.getsize(compressed_path)
                
                # Update attachment record
                attachment.compressed_path = compressed_path
                attachment.compressed_size = compressed_size
                self.db.commit()
                
                logger.info(f"Compressed attachment {attachment_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to compress attachment {attachment_id}: {e}")
            return False