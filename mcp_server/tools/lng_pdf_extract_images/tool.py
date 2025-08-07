import os
import fitz  # PyMuPDF
from PIL import Image
import io
from typing import Dict, Any
import mcp.types as types


def lng_pdf_extract_images(pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Extracts all images from a PDF file and saves them to a specified directory.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str, optional): Directory to save extracted images. 
                                   If None, creates a folder next to the PDF file
    
    Returns:
        Dict[str, Any]: Result containing success status, message, and extracted images info
    """
    try:
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            return {
                "success": False,
                "message": f"PDF file not found: {pdf_path}",
                "extracted_images": []
            }
        
        # Set output directory if not specified
        if output_dir is None:
            pdf_dir = os.path.dirname(pdf_path)
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_dir = os.path.join(pdf_dir, f"{pdf_name}_images")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Open PDF document
        pdf_document = fitz.open(pdf_path)
        extracted_images = []
        image_count = 0
        total_pages = len(pdf_document)
        
        # Iterate through each page
        for page_num in range(total_pages):
            page = pdf_document.load_page(page_num)
            image_list = page.get_images(full=True)
            
            # Extract each image from the page
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    # Skip images with alpha channel for now
                    if pix.n - pix.alpha < 4:
                        # Generate filename
                        image_count += 1
                        img_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                        img_path = os.path.join(output_dir, img_filename)
                        
                        # Save image
                        if pix.n - pix.alpha == 1:  # Grayscale
                            pix.save(img_path)
                        else:  # RGB
                            pix.save(img_path)
                        
                        extracted_images.append({
                            "filename": img_filename,
                            "path": img_path,
                            "page": page_num + 1,
                            "size": f"{pix.width}x{pix.height}",
                            "colorspace": pix.colorspace.name if pix.colorspace else "Unknown"
                        })
                    else:
                        # Convert CMYK to RGB
                        pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                        image_count += 1
                        img_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                        img_path = os.path.join(output_dir, img_filename)
                        pix_rgb.save(img_path)
                        
                        extracted_images.append({
                            "filename": img_filename,
                            "path": img_path,
                            "page": page_num + 1,
                            "size": f"{pix_rgb.width}x{pix_rgb.height}",
                            "colorspace": "RGB (converted)"
                        })
                        pix_rgb = None
                    
                    pix = None
                    
                except Exception as e:
                    print(f"Error extracting image {img_index + 1} from page {page_num + 1}: {str(e)}")
                    continue
        
        pdf_document.close()
        
        return {
            "success": True,
            "message": f"Successfully extracted {len(extracted_images)} images from {total_pages} pages",
            "output_directory": output_dir,
            "total_images": len(extracted_images),
            "extracted_images": extracted_images
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing PDF: {str(e)}",
            "extracted_images": []
        }


# MCP tool wrapper
def tool_lng_pdf_extract_images(pdf_path: str, output_dir: str = None) -> str:
    """
    MCP tool wrapper for PDF image extraction.
    
    Args:
        pdf_path (str): Path to the PDF file to extract images from
        output_dir (str, optional): Directory where extracted images will be saved
    
    Returns:
        str: Formatted result message
    """
    result = lng_pdf_extract_images(pdf_path, output_dir)
    
    if result["success"]:
        message = f"✅ {result['message']}\n"
        message += f"📁 Output directory: {result['output_directory']}\n"
        message += f"📊 Total images extracted: {result['total_images']}\n\n"
        
        if result["extracted_images"]:
            message += "📸 Extracted images:\n"
            for img in result["extracted_images"]:
                message += f"  • {img['filename']} (Page {img['page']}, {img['size']}, {img['colorspace']})\n"
        
        return message
    else:
        return f"❌ {result['message']}"


# Tool metadata for MCP registration
TOOL_NAME = "lng_pdf_extract_images"
TOOL_DESCRIPTION = "Extracts all images from a PDF file and saves them to a specified directory."


# MCP required functions
async def tool_info():
    """Return tool information for MCP."""
    return {
        "description": f"""{TOOL_DESCRIPTION}

**Parameters:**
- `pdf_path` (string, required): Path to the PDF file to extract images from
- `output_dir` (string, optional): Directory where extracted images will be saved

**Example Usage:**
- Provide a path to a PDF file to extract all images
- Optionally specify output directory, otherwise creates folder next to PDF
- The system will extract all images and save them as PNG files

This tool is useful for extracting images from PDF documents for further processing or analysis.""",
        "schema": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Path to the PDF file to extract images from"
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory where extracted images will be saved (optional)"
                }
            },
            "required": ["pdf_path"]
        }
    }


async def run_tool(name: str, parameters: dict) -> list[types.Content]:
    """Run the tool with provided parameters."""
    try:
        pdf_path = parameters.get("pdf_path")
        output_dir = parameters.get("output_dir")
        
        if not pdf_path:
            return [types.TextContent(type="text", text='{"error": "pdf_path is required"}')]
        
        result = tool_lng_pdf_extract_images(pdf_path, output_dir)
        return [types.TextContent(type="text", text=result)]
        
    except Exception as e:
        error_result = f'{{"error": "Error processing PDF: {str(e)}"}}'
        return [types.TextContent(type="text", text=error_result)]


if __name__ == "__main__":
    # Test the tool
    test_pdf = input("Enter PDF path to test: ")
    if test_pdf:
        result = tool_lng_pdf_extract_images(test_pdf)
        print(result)
