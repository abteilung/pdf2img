# test2.pdf

This is a binary file of the type: PDF

# test.pdf

This is a binary file of the type: PDF

# requirements.txt

```txt
Flask==2.0.1
Werkzeug==2.0.1
pdf2image==1.16.0
Pillow==8.3.1
redis==3.5.3
gunicorn==20.1.0
```

# docker-compose.yaml

```yaml
version: '3'

services:
    web:
        build: .
        ports:
            - '5005:5000'
        volumes:
            - .:/usr/src/app
        depends_on:
            - redis
        environment:
            - FLASK_ENV=production

    redis:
        image: 'redis:alpine'
        ports:
            - '6179:6379'

```

# README.md

```md
# PDF to Image Conversion Service Documentation

This service provides functionality to convert PDF pages to images, serve these images with various transformations, and generate responsive image HTML.

## Endpoints

### 1. Convert PDF to Image

**Endpoint:** `/convert`
**Method:** POST

Convert a page from a PDF file to an image.

**Parameters:**

-   `file`: The PDF file (multipart/form-data)
-   `page`: Page number to convert (default: 1)

**Response:**

\`\`\`json
{
	"id": "unique_filename",
	"original_filename": "uploaded_file.pdf",
	"page": 1,
	"url": "http://server-address:5000/image/unique_filename"
}
\`\`\`

### 2. Serve Image

**Endpoint:** `/image/<filename>`
**Method:** GET

Serve an image with optional transformations.

**Query Parameters:**

-   `format`: Image format (default: webp)
-   `width`: Resize width
-   `height`: Resize height
-   `crop_width`: Width to crop the image
-   `crop_height`: Height to crop the image
-   `focus_x`: Horizontal focus point for cropping (0 to 1, default: 0.5)
-   `focus_y`: Vertical focus point for cropping (0 to 1, default: 0.5)

**Example:**

\`\`\`
/image/abc123?format=jpg&width=800&height=600&crop_width=500&crop_height=300&focus_x=0.3&focus_y=0.7
\`\`\`

### 3. Responsive Image HTML

**Endpoint:** `/responsive/<filename>`
**Method:** GET

Generate HTML for a responsive image tag.

**Query Parameters:**

-   `crop_width`: Width to crop the image
-   `crop_height`: Height to crop the image
-   `focus_x`: Horizontal focus point for cropping (0 to 1, default: 0.5)
-   `focus_y`: Vertical focus point for cropping (0 to 1, default: 0.5)

**Example:**

\`\`\`
/responsive/abc123?crop_width=800&crop_height=600&focus_x=0.3&focus_y=0.2
\`\`\`

**Response:** HTML string with `<img>` tag including `srcset` and `sizes` attributes.

## Features

1. **PDF Conversion:** Convert specific pages of PDF files to images.
2. **Image Resizing:** Resize images to specified dimensions.
3. **Format Conversion:** Convert images to different formats (e.g., WebP, JPEG, PNG).
4. **Image Cropping:** Crop images to specified dimensions with adjustable focus points.
5. **Responsive Images:** Generate HTML for responsive images with appropriate `srcset` and `sizes` attributes.
6. **Caching:** Redis-based caching for improved performance.

## Usage Examples

1. **Convert a PDF page to an image:**

    \`\`\`
    curl -X POST -F "file=@document.pdf" -F "page=1" http://server-address:5000/convert
    \`\`\`

2. **Serve a resized and cropped image:**

    \`\`\`
    http://server-address:5000/image/abc123?width=800&height=600&crop_width=500&crop_height=300&focus_x=0.3&focus_y=0.7&format=webp
    \`\`\`

3. **Get responsive image HTML:**
    \`\`\`
    http://server-address:5000/responsive/abc123?crop_width=800&crop_height=600&focus_x=0.3&focus_y=0.2
    \`\`\`

## Notes

-   The service uses WebP as the default image format for better compression and faster loading times.
-   Responsive images are generated with breakpoints at 320px, 480px, 640px, 768px, 1024px, 1280px, and 1536px widths.
-   Images are cached in Redis for 24 hours to improve performance for repeated requests.
-   The service uses lazy loading for responsive images to optimize page load times.

For any issues or feature requests, please contact the development team.

```

# Dockerfile

```
FROM python:3.9

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/usr/src/app
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--log-level", "debug", "wsgi:app"]
```

# .gitignore

```
# Python
__pycache__
*.py[cod]
*$py.class

# Virtual Environment
venv/
env/
.env

# Flask
instance/
.webassets-cache

# Logs
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/

# Docker
.docker/

# Uploaded and generated files
uploads/
*.pdf.img

# Redis dump file
dump.rdb

# Temporary files
*.tmp

# Package files
*.egg
*.egg-info/
dist/
build/
eggs/
parts/
var/
sdist/
develop-eggs/
.installed.cfg
lib/
lib64/
```

# .dockerignore

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class

# Virtual Environment
venv/
env/
.env

# Logs
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/

# Docker
Dockerfile
.dockerignore

# Uploaded and generated files
uploads/
*.pdf.img

# Redis dump file
dump.rdb

# Temporary files
*.tmp

# Documentation
README.md

# Test files
tests/

# Configuration files that should not be in the image
*.yml
*.yaml
!docker-compose.yml

# Any local development files
*.dev
```

# src/wsgi.py

```py
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
```

# src/app.py

```py
from flask import Flask, request, jsonify, send_file, make_response, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import pdf2image
from PIL import Image
import io
import os
import hashlib
import time
import redis

def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize Redis
    redis_client = redis.Redis(host='redis', port=6379, db=0)

    UPLOAD_FOLDER = '/usr/src/app/uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


    def resize_image(img, width=None, height=None):
        if width and height:
            return img.resize((width, height), Image.LANCZOS)
        elif width:
            ratio = width / img.width
            return img.resize((width, int(img.height * ratio)), Image.LANCZOS)
        elif height:
            ratio = height / img.height
            return img.resize((int(img.width * ratio), height), Image.LANCZOS)
        return img

    def crop_image(img, crop_width, crop_height, focus_x, focus_y):
        width, height = img.size
        
        crop_ratio = crop_width / crop_height
        img_ratio = width / height

        if crop_ratio > img_ratio:
            new_height = int(width / crop_ratio)
            top = int((height - new_height) * focus_y)
            bottom = top + new_height
            crop_box = (0, top, width, bottom)
        else:
            new_width = int(height * crop_ratio)
            left = int((width - new_width) * focus_x)
            right = left + new_width
            crop_box = (left, 0, right, height)

        return img.crop(crop_box)

    @app.route('/convert', methods=['POST'])
    def convert_pdf_to_image():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        page = request.form.get('page', 1, type=int)

        filename = hashlib.md5(f"{file.filename}{page}{time.time()}".encode()).hexdigest()
        image_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf.img")

        if not os.path.exists(image_path):
            images = pdf2image.convert_from_bytes(file.read(), first_page=page, last_page=page)
            if not images:
                return jsonify({'error': 'Failed to convert PDF'}), 500
            images[0].save(image_path, format='PNG')

        image_url = url_for('serve_image', filename=filename, _external=True)
        return jsonify({
            'id': filename,
            'original_filename': file.filename,
            'page': page,
            'url': image_url
        })

    @app.route('/image/<string:filename>')
    def serve_image(filename):
        format = request.args.get('format', 'webp').lower()
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        crop_width = request.args.get('crop_width', type=int)
        crop_height = request.args.get('crop_height', type=int)
        focus_x = request.args.get('focus_x', 0.5, type=float)
        focus_y = request.args.get('focus_y', 0.5, type=float)
        
        cache_key = f"{filename}_{format}_{width}_{height}_{crop_width}_{crop_height}_{focus_x}_{focus_y}"
        
        cached_image = redis_client.get(cache_key)
        if cached_image:
            img_io = io.BytesIO(cached_image)
            return send_file(img_io, mimetype=f'image/{format}')

        image_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf.img")
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image not found'}), 404

        img = Image.open(image_path)
        
        if crop_width and crop_height:
            img = crop_image(img, crop_width, crop_height, focus_x, focus_y)
        
        if width or height:
            img = resize_image(img, width, height)
        
        img_io = io.BytesIO()
        img.save(img_io, format=format.upper())
        img_io.seek(0)
        
        redis_client.setex(cache_key, 86400, img_io.getvalue())  # Cache for 24 hours
        
        response = make_response(send_file(img_io, mimetype=f'image/{format}'))
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
        return response

    @app.route('/responsive/<string:filename>')
    def responsive_image(filename):
        image_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf.img")
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image not found'}), 404

        with Image.open(image_path) as img:
            original_width, original_height = img.size

        crop_width = request.args.get('crop_width', type=int)
        crop_height = request.args.get('crop_height', type=int)
        focus_x = request.args.get('focus_x', 0.5, type=float)
        focus_y = request.args.get('focus_y', 0.5, type=float)

        if crop_width and crop_height:
            aspect_ratio = crop_width / crop_height
            display_width, display_height = crop_width, crop_height
        else:
            aspect_ratio = original_width / original_height
            display_width, display_height = original_width, original_height

        base_url = url_for('serve_image', filename=filename, _external=True)

        breakpoints = [320, 480, 640, 768, 1024, 1280, 1536]
        srcset = []

        for bp in breakpoints:
            if bp > display_width:
                break
            height = int(bp / aspect_ratio)
            crop_params = f"&crop_width={crop_width}&crop_height={crop_height}" if crop_width and crop_height else ""
            focus_params = f"&focus_x={focus_x}&focus_y={focus_y}"
            srcset.append(f"{base_url}?width={bp}&height={height}{crop_params}{focus_params}&format=webp {bp}w")

        srcset_string = ", ".join(srcset)

        sizes = [
            "(max-width: 320px) 320px",
            "(max-width: 480px) 480px",
            "(max-width: 640px) 640px",
            "(max-width: 768px) 768px",
            "(max-width: 1024px) 1024px",
            "(max-width: 1280px) 1280px",
            "1536px"
        ]
        sizes_string = ", ".join(sizes)

        default_src = f"{base_url}?width={display_width}&height={display_height}"
        if crop_width and crop_height:
            default_src += f"&crop_width={crop_width}&crop_height={crop_height}&focus_x={focus_x}&focus_y={focus_y}"
        default_src += "&format=webp"

        html = f"""
        <img src="{default_src}" 
            srcset="{srcset_string}" 
            sizes="{sizes_string}"
            width="{display_width}"
            height="{display_height}"
            alt="Responsive image"
            loading="lazy">
        """
        
        return html
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

```

# uploads/87324ee46df3ea6d2972083b333a5705.pdf.img

This is a binary file of the type: Binary

# uploads/787d094eb5c290662554b12aa000bc1d.pdf.img

This is a binary file of the type: Binary

