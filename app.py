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

def rotate_image(image_path, angle):
    img = Image.open(image_path)
    rotated = img.rotate(int(angle), expand=True)
    return rotated

def create_color_histogram(img):
    plt.figure(figsize=(6, 4))
    colors = ('r', 'g', 'b')
    for i, color in enumerate(colors):
        hist = np.array(img)[:, :, i].flatten()
        plt.hist(hist, bins=256, color=color, alpha=0.5)
    plt.title('Color Distribution')
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
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
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        rotated_img = rotate_image(upload_path, angle)
        rotated_path = os.path.join(app.config['UPLOAD_FOLDER'], 'rotated_' + filename)
        rotated_img.save(rotated_path)

        orig_hist = create_color_histogram(Image.open(upload_path))
        rotated_hist = create_color_histogram(rotated_img)

        return render_template('result.html',
                               original=upload_path,
                               rotated=rotated_path,
                               angle=angle,
                               orig_hist=orig_hist,
                               rotated_hist=rotated_hist)
    return 'Invalid file type'

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)