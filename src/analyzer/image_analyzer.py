import google.generativeai as genai
from PIL import Image
import io
from typing import Dict, Any, List, Optional
import fitz
from dataclasses import dataclass
import json

@dataclass
class DiagramType:
    name: str
    keywords: List[str]
    template: str

class ImageAnalyzer:
    DIAGRAM_TYPES = {
        'flowchart': DiagramType(
            name='flowchart',
            keywords=['flow', 'process', 'workflow', 'steps'],
            template='flowchart TD'
        ),
        'sequence': DiagramType(
            name='sequence',
            keywords=['sequence', 'interaction', 'timeline'],
            template='sequenceDiagram'
        ),
        'class': DiagramType(
            name='class',
            keywords=['class', 'object', 'uml', 'inheritance'],
            template='classDiagram'
        ),
        'mindmap': DiagramType(
            name='mindmap',
            keywords=['mind map', 'concept', 'hierarchy'],
            template='mindmap'
        )
    }

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        self.text_model = genai.GenerativeModel('gemini-pro')

    async def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        prompt = """
        Analyze this image and provide the following information in JSON format:
        {
            'type': 'diagram/chart/table/image',
            'description': 'detailed description',
            'text_content': 'any text in the image',
            'structure': 'description of the visual structure',
            'can_convert_to_mermaid': true/false,
            'suggested_diagram_type': 'flowchart/sequence/class/etc'
        }
        Focus on identifying if this is a type of diagram that could be represented using Mermaid.
        """

        response = await self.vision_model.generate_content([prompt, image])
        result = json.loads(response.text)

        if result.get('can_convert_to_mermaid'):
            mermaid_code = await self._generate_mermaid_code(
                image,
                result['description'],
                result['suggested_diagram_type']
            )
            result['mermaid_code'] = mermaid_code

        return result

    async def _generate_mermaid_code(self, image: Image.Image, description: str, diagram_type: str) -> str:
        prompt = f"""
        Based on this {diagram_type} diagram, generate Mermaid code that represents its structure.
        Description: {description}
        
        Focus on maintaining the logical structure and relationships shown in the diagram.
        Return only the Mermaid code without any explanation or markdown formatting.
        """

        response = await self.vision_model.generate_content([prompt, image])
        return response.text.strip()

    def extract_images_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_idx, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image['image']
                
                try:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    images.append({
                        'page': page_num + 1,
                        'index': img_idx,
                        'image': pil_image,
                        'bbox': self._get_image_bbox(page, img)
                    })
                except Exception as e:
                    print(f'Error processing image: {str(e)}')

        return images

    def _get_image_bbox(self, page, img) -> Dict[str, float]:
        # Get image bounding box implementation
        return {'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0}
