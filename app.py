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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def rotate_image(image_path, angle, red_angle=0, green_angle=0, blue_angle=0):
    img = Image.open(image_path)
    
    # Если заданы углы для отдельных каналов
    if red_angle or green_angle or blue_angle:
        # Конвертируем в RGB если нужно
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Разделяем на каналы
        r, g, b = img.split()
        
        # Поворачиваем каждый канал на свой угол
        if red_angle:
            r = r.rotate(float(red_angle), expand=True)
        if green_angle:
            g = g.rotate(float(green_angle), expand=True)
        if blue_angle:
            b = b.rotate(float(blue_angle), expand=True)
        
        # Объединяем каналы обратно
        rotated = Image.merge('RGB', (r, g, b))
        
        # Применяем общий поворот если задан
        if angle and float(angle) != 0:
            rotated = rotated.rotate(float(angle), expand=True)
    else:
        # Обычный поворот всей картинки
        rotated = img.rotate(float(angle), expand=True)
    
    return rotated

def create_color_histogram(img):
    plt.figure(figsize=(6, 4))
    
    # Конвертируем в RGB если нужно
    if img.mode != 'RGB':
        img_rgb = img.convert('RGB')
    else:
        img_rgb = img
    
    img_array = np.array(img_rgb)
    
    colors = ('r', 'g', 'b')
    for i, color in enumerate(colors):
        hist = img_array[:, :, i].flatten()
        plt.hist(hist, bins=256, color=color, alpha=0.5, label=f'{color.upper()} channel')
    
    plt.title('Color Distribution')
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
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
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Поворачиваем изображение
        rotated_img = rotate_image(upload_path, angle, red_angle, green_angle, blue_angle)
        rotated_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated_' + filename)
        rotated_img.save(rotated_path)

        # Создаем гистограммы
    return 'Invalid file type'

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)