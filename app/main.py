from flask import Flask, request, jsonify, send_file, make_response, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import pdf2image
from PIL import Image
import io
import os
import hashlib
import time
import redis

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

UPLOAD_FOLDER = '/app/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

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
    
    # Calculate the crop box
    crop_ratio = crop_width / crop_height
    img_ratio = width / height

    if crop_ratio > img_ratio:
        # Crop the height
        new_height = int(width / crop_ratio)
        top = int((height - new_height) * focus_y)
        bottom = top + new_height
        crop_box = (0, top, width, bottom)
    else:
        # Crop the width
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
        'id': filename,  # Added comma here
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
    
    # Generate a cache key based on all parameters
    cache_key = f"{filename}_{format}_{width}_{height}_{crop_width}_{crop_height}_{focus_x}_{focus_y}"
    
    # Try to get the image from Redis cache
    cached_image = redis_client.get(cache_key)
    if cached_image:
        img_io = io.BytesIO(cached_image)
        return send_file(img_io, mimetype=f'image/{format}')

    image_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf.img")
    
    if not os.path.exists(image_path):
        return jsonify({'error': 'Image not found'}), 404

    img = Image.open(image_path)
    
    # Apply cropping if specified
    if crop_width and crop_height:
        img = crop_image(img, crop_width, crop_height, focus_x, focus_y)
    
    # Apply resizing if specified
    if width or height:
        img = resize_image(img, width, height)
    
    img_io = io.BytesIO()
    img.save(img_io, format=format.upper())
    img_io.seek(0)
    
    # Cache the image in Redis
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

    # Get cropping parameters
    crop_width = request.args.get('crop_width', type=int)
    crop_height = request.args.get('crop_height', type=int)
    focus_x = request.args.get('focus_x', 0.5, type=float)
    focus_y = request.args.get('focus_y', 0.5, type=float)

    # If cropping is specified, use crop dimensions, otherwise use original
    if crop_width and crop_height:
        aspect_ratio = crop_width / crop_height
        display_width, display_height = crop_width, crop_height
    else:
        aspect_ratio = original_width / original_height
        display_width, display_height = original_width, original_height

    base_url = url_for('serve_image', filename=filename, _external=True)

    # Define breakpoints and their corresponding image widths
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

    # Calculate sizes attribute
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

    # Use the display dimensions for the src attribute
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
