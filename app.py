from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rotate_image(image_path, angle, red_angle=0, green_angle=0, blue_angle=0):
    """Rotate image with optional per-channel rotation"""
    try:
        img = Image.open(image_path)
        angle = float(angle) if angle else 0
        red_angle = float(red_angle) if red_angle else 0
        green_angle = float(green_angle) if green_angle else 0
        blue_angle = float(blue_angle) if blue_angle else 0
        
        # Check if any channel rotation is requested
        if red_angle != 0 or green_angle != 0 or blue_angle != 0:
            # Convert to RGB if needed
            if img.mode not in ['RGB', 'RGBA']:
                if img.mode == 'P':
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
            
            # Handle RGBA images (preserve alpha channel)
            if img.mode == 'RGBA':
                r, g, b, a = img.split()
            else:
                r, g, b = img.split()
                a = None
            
            # Rotate each channel individually
            if red_angle != 0:
                r = r.rotate(red_angle, expand=True, resample=Image.BICUBIC)
            if green_angle != 0:
                g = g.rotate(green_angle, expand=True, resample=Image.BICUBIC)
            if blue_angle != 0:
                b = b.rotate(blue_angle, expand=True, resample=Image.BICUBIC)
            if a is not None:
                a = a.rotate(angle, expand=True, resample=Image.BICUBIC)
            
            # Merge channels back
            if a is not None:
                rotated = Image.merge('RGBA', (r, g, b, a))
            else:
                rotated = Image.merge('RGB', (r, g, b))
            
            # Apply overall rotation if any channel was rotated and angle is different
            if angle != 0 and (red_angle != angle or green_angle != angle or blue_angle != angle):
                rotated = rotated.rotate(angle, expand=True, resample=Image.BICUBIC)
        else:
            # Normal rotation - rotate entire image
            rotated = img.rotate(angle, expand=True, resample=Image.BICUBIC)
        
        return rotated
    except Exception as e:
        raise Exception(f"Error rotating image: {str(e)}")

def create_color_histogram(img):
    """Create and return base64 encoded color histogram image"""
    try:
        plt.figure(figsize=(8, 5))
        
        # Convert to RGB if needed
        if img.mode not in ['RGB', 'RGBA']:
            img_rgb = img.convert('RGB')
        elif img.mode == 'RGBA':
            # Convert RGBA to RGB
            img_rgb = Image.new('RGB', img.size, (255, 255, 255))
            img_rgb.paste(img, mask=img.split()[3])
        else:
            img_rgb = img
        
        img_array = np.array(img_rgb)
        
        # Create histogram for each channel
        colors = ('r', 'g', 'b')
        channel_names = ('Red', 'Green', 'Blue')
        
        for i, (color, name) in enumerate(zip(colors, channel_names)):
            hist = img_array[:, :, i].flatten()
            plt.hist(hist, bins=128, color=color, alpha=0.7, 
                    label=f'{name} Channel', density=True, edgecolor='black', linewidth=0.5)
        
        plt.title('Color Channel Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Pixel Intensity (0-255)', fontsize=12)
        plt.ylabel('Normalized Frequency', fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error creating histogram: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return 'No file part'
        
        file = request.files['file']
        angle = request.form.get('angle', 0)
        red_angle = request.form.get('red_angle', 0)
        green_angle = request.form.get('green_angle', 0)
        blue_angle = request.form.get('blue_angle', 0)
        
        if file.filename == '':
            return 'No selected file'
        
        if file and allowed_file(file.filename):
            # Создаем директорию для загрузок, если она не существует
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            
            filename = secure_filename(file.filename)
            upload_path = os.path.join(upload_dir, filename)
            file.save(upload_path)

            # Rotate image with channel options
            rotated_img = rotate_image(upload_path, angle, red_angle, green_angle, blue_angle)
            
            # Save rotated image
            rotated_filename = f"rotated_{os.path.splitext(filename)[0]}_{angle}"
            if red_angle != 0 or green_angle != 0 or blue_angle != 0:
                rotated_filename += f"_R{red_angle}_G{green_angle}_B{blue_angle}"
            rotated_filename += os.path.splitext(filename)[1]
            rotated_path = os.path.join(upload_dir, rotated_filename)
            rotated_img.save(rotated_path)

            # Create histograms
            orig_img = Image.open(upload_path)
            orig_hist = create_color_histogram(orig_img)
            rotated_hist = create_color_histogram(rotated_img)

            return render_template('result.html',
                                   original=upload_path.replace('\\', '/'),
                                   rotated=rotated_path.replace('\\', '/'),
                                   angle=angle,
                                   red_angle=red_angle,
                                   green_angle=green_angle,
                                   blue_angle=blue_angle,
                                   orig_hist=orig_hist,
                                   rotated_hist=rotated_hist)
        
        return 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP'
    
    except Exception as e:
        return f'Error processing image: {str(e)}'

def create_directories():
    """Create necessary directories on startup"""
    try:
        # Create upload directory
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create static directory
        static_dir = 'static'
        os.makedirs(static_dir, exist_ok=True)
        
        print(f"Directories created: {upload_dir}, {static_dir}")
    except Exception as e:
        print(f"Error creating directories: {str(e)}")

if __name__ == '__main__':
    create_directories()
    app.run(debug=True)