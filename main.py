import cv2
import numpy as np
from image_processor import ImageProcessor
from constants import ImageClass
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
import random
import string

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_image", methods=["POST"])
def process_image():
    DEFAULT_KERNEL_SIZE = 20
    DEFAULT_THRESHOLD_BINARY_IMAGE = 128
    DEFAULT_THRESHOLD_REGION_SELECTION = 3

    # Parse parameters
    kernel_size = int(request.form["kernel_size"]) if request.form["kernel_size"] != "" else DEFAULT_KERNEL_SIZE
    threshold_binary_image = int(request.form["threshold_binary_image"]) if request.form["threshold_binary_image"] != "" \
        else DEFAULT_THRESHOLD_BINARY_IMAGE
    threshold_region_selection = int(request.form["threshold_region_selection"]) if \
        request.form["threshold_region_selection"] != "" else DEFAULT_THRESHOLD_REGION_SELECTION
    original_image = request.files["image"]

    # Process image
    extension = original_image.filename.split(".")[1]
    original_image.save("static/image_original." + extension)

    # 1. Open image with OpenCV
    image = cv2.imread("static/image_original." + extension)
    height, width = image.shape[0], image.shape[1]
    threshold_region_selection = threshold_region_selection / 100 * height * width

    # 2. Convert image to gray
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("static/image_gray." + extension, image)

    # 3. Remove noises
    image = cv2.erode(image, np.ones((kernel_size, kernel_size), np.int))
    cv2.imwrite("static/image_eroded." + extension, image)

    # 4. Get binary image
    image = ImageProcessor.get_binary_image(_image=image, _threshold=threshold_binary_image)
    cv2.imwrite("static/image_binary." + extension, image)

    # 5. Region selection
    regions = ImageProcessor.get_wanted_regions(image)
    image = ImageProcessor.get_binary_image(_image=image, _threshold=0)
    for region in regions:
        if len(region) >= threshold_region_selection:
            for pixel in region:
                y, x = pixel[0], pixel[1]
                image[y][x] = 0
    cv2.imwrite("static/image_selected_region." + extension, image)

    # 6. Classify image
    result = ImageClass.get_class(ImageProcessor.classify(image))

    dummy_url_param = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    dummy_url_param = "?d=" + dummy_url_param
    data = {
        "0": "static/image_original." + extension + dummy_url_param,
        "1": "static/image_gray." + extension + dummy_url_param,
        "2": "static/image_eroded." + extension + dummy_url_param,
        "3": "static/image_binary." + extension + dummy_url_param,
        "4": "static/image_selected_region." + extension + dummy_url_param,
        "class": result
    }

    return jsonify(data)
