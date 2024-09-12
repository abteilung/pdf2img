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

```json
{
	"id": "unique_filename",
	"original_filename": "uploaded_file.pdf",
	"page": 1,
	"url": "http://server-address:5000/image/unique_filename"
}
```

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

```
/image/abc123?format=jpg&width=800&height=600&crop_width=500&crop_height=300&focus_x=0.3&focus_y=0.7
```

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

```
/responsive/abc123?crop_width=800&crop_height=600&focus_x=0.3&focus_y=0.2
```

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

    ```
    curl -X POST -F "file=@document.pdf" -F "page=1" http://server-address:5000/convert
    ```

2. **Serve a resized and cropped image:**

    ```
    http://server-address:5000/image/abc123?width=800&height=600&crop_width=500&crop_height=300&focus_x=0.3&focus_y=0.7&format=webp
    ```

3. **Get responsive image HTML:**
    ```
    http://server-address:5000/responsive/abc123?crop_width=800&crop_height=600&focus_x=0.3&focus_y=0.2
    ```

## Notes

-   The service uses WebP as the default image format for better compression and faster loading times.
-   Responsive images are generated with breakpoints at 320px, 480px, 640px, 768px, 1024px, 1280px, and 1536px widths.
-   Images are cached in Redis for 24 hours to improve performance for repeated requests.
-   The service uses lazy loading for responsive images to optimize page load times.

For any issues or feature requests, please contact the development team.
