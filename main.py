import cv2
import numpy as np
from image_processor import ImageProcessor
from constants import ImageClass, ThresholdRecommendation
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
import random
import string
import copy

app = Flask(__name__)

STATIC_FILES_PATH = "./static/"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_image", methods=["POST"])
def process_image():
    # PROSES 1: Request diterima oleh API pada webserver

    # Nilai-nilai berikut adalah nilai default yang digunakan ketika parameter-parameter request tidak dilengkapi
    DEFAULT_KERNEL_SIZE = 20
    DEFAULT_THRESHOLD_BINARY_IMAGE = 128
    DEFAULT_THRESHOLD_REGION_SELECTION = 3
    THRESHOLD_FIXING_UNIT = DEFAULT_THRESHOLD_BINARY_IMAGE / 2

    # PROSES 2: Parameter-parameter request diperoleh
    # Terdapat tiga parameter yang akan diperoleh, yakni:
    # 1. kernel_size, diperlukan sebagai ukuran kernel untuk melakukan operasi erosi
    # 2. threshold_binary_image, diperlukan sebagai threshold untuk mengubah gambar menjadi binary (hitam atau putih / 0 atau 255)
    # 3. threshold_region_selection, diperlukan sebagai threshold untuk memilih region tertentu pada gambar binary berdasarkan ukuran dari region tersebut
    kernel_size = int(request.form["kernel_size"]) if request.form["kernel_size"] != "" else DEFAULT_KERNEL_SIZE
    threshold_binary_image = int(request.form["threshold_binary_image"]) if request.form["threshold_binary_image"] != "" \
        else DEFAULT_THRESHOLD_BINARY_IMAGE
    threshold_region_selection = int(request.form["threshold_region_selection"]) if \
        request.form["threshold_region_selection"] != "" else DEFAULT_THRESHOLD_REGION_SELECTION
    original_image = request.files["image"]

    # PROSES 3: Gambar disimpan pada direktori static
    # Tujuan gambar ini disimpan agar nanti dapat dibuka lagi untuk pemrosesan. Gambar disimpan dengan nama image_original.
    # Jika sudah ada gambar dengan nama image_original, maka gambar tersebut akan ditimpa (overwrite).
    extension = original_image.filename.split(".")[1]
    original_image.save(STATIC_FILES_PATH + "image_original." + extension)

    # PROSES 4: Gambar dibuka dengan OpenCV
    image = cv2.imread(STATIC_FILES_PATH + "image_original." + extension)
    height, width = image.shape[0], image.shape[1]
    threshold_region_selection = threshold_region_selection / 100 * height * width

    # PROSES 5: Mode gambar diubah menjadi grayscale dan gambar hasil disimpan
    # Tujuan mode gambar diubah menjadi grayscale adalah agar gambar lebih mudah diproses.
    # Ketika gambar bermode RGB, piksel-pikselnya memiliki tiga channel warna, yakni Red, Green, dan Blue.
    # Untuk menyederhanakannya, gambar diubah menjadi mode grayscale.
    # Dengan mode grayscale, piksel-piksel gambar hanya memiliki satu channel warna, yakni intensitas cahaya saja.
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(STATIC_FILES_PATH + "image_gray." + extension, image)

    # PROSES 6: Penerapan operasi erosi pada gambar dan gambar hasil disimpan
    # Operasi erosi adalah salah satu operasi morfologi pada gambar. Selain operasi erosi, terdapat operasi dilasi.
    # Operasi erosi bertujuan untuk menghilangkan noises pada gambar dan membuat fitur gambar yang diinginkan, yakni keretakan jalan, menjadi lebih besar.
    image = cv2.erode(image, np.ones((kernel_size, kernel_size), np.int))
    cv2.imwrite(STATIC_FILES_PATH + "image_eroded." + extension, image)

    while True:
        print("Attempting threshold {0}".format(threshold_binary_image))
        copied_image = copy.deepcopy(image)
        # PROSES 7: Mengubah gambar menjadi binary dan gambar hasil disimpan
        # Gambar binary adalah gambar yang piksel-pikselnya hanya memiliki dua kemungkinan warna, yakni hitam atau putih / 0 atau 255.
        # Hal ini dilakukan dengan melakukan thresholding. Nilai threshold ditentukan oleh pengguna.
        # Pada program ini, nilai default threshold telah ditentukan.
        # Jika piksel memiliki nilai dibawah threshold, maka nilai piksel tersebut diubah menjadi 0.
        # Jika piksel memiliki nilai diatas threshold, maka nilai piksel tersebut diubah menjadi 255.
        copied_image = ImageProcessor.get_binary_image(_image=copied_image, _threshold=threshold_binary_image)
        cv2.imwrite(STATIC_FILES_PATH + "image_binary." + extension, copied_image)

        # PROSES 8: Menyeleksi region pada binary image dan gambar hasil disimpan
        # Seleksi region dilakukan pada binary image untuk mendapatkan fitur yang benar-benar diinginkan untuk klasifikasi, yakni keretakan jalan itu sendiri.
        # Pada Proses 7, ketika diperoleh gambar binary, keretakan jalan masih belum teridentifikasi karena masih terdapat banyak region dalam gambar.
        # Dengan demikian, perlu dipilih region yang memiliki besar diatas threshold agar region yang tersisa pada gambar adalah keretakan jalan.
        # Nilai threshold ini ditentukan oleh masukan dari pengguna. Jika pengguna tidak memberi masukan, maka digunakan nilai default.
        regions = ImageProcessor.get_wanted_regions(copied_image)
        copied_image = ImageProcessor.get_binary_image(_image=copied_image, _threshold=0)
        for region in regions:
            if len(region) >= threshold_region_selection:
                for pixel in region:
                    y, x = pixel[0], pixel[1]
                    copied_image[y][x] = 0

        threshold_recommendation = ImageProcessor.is_binary_image_appropriate_for_classification(copied_image)
        if threshold_recommendation == ThresholdRecommendation.NONE:
            image = copied_image
            cv2.imwrite(STATIC_FILES_PATH + "image_selected_region." + extension, image)
            break
        else:
            if threshold_recommendation == ThresholdRecommendation.UP:
                threshold_binary_image = threshold_binary_image + THRESHOLD_FIXING_UNIT
                print("UP threshold becomes {0}".format(threshold_binary_image))
            elif threshold_recommendation == ThresholdRecommendation.DOWN:
                threshold_binary_image = threshold_binary_image - THRESHOLD_FIXING_UNIT
                print("DOWN threshold becomes {0}".format(threshold_binary_image))
            THRESHOLD_FIXING_UNIT = THRESHOLD_FIXING_UNIT / 2
            del copied_image

    # PROSES 9: Klasifikasi gambar berdasar hasil seleksi region
    # Klasifikasi bertujuan untuk menentukan apakah keretakan jalan berjenis TRAVERSAL, LONGITUDINAL, atau TURTLE.
    # Klasifikasi dilakukan menggunakan hasil pada Proses 8.
    # Jika gambar hasil Proses 8 memiliki region di bagian kiri dan kanan dan tidak memiliki region di bagian atas dan bawah, maka jenis keretakan adalah TRAVERSAL.
    # Jika gambar hasil Proses 8 memiliki region di bagian atas dan bawah dan tidak memiliki region di bagian kiri dan kanan, maka jenis keretakan adalah LONGITUDINAL.
    # Jika gambar hasil Proses 8 memiliki region di bagian atas, kanan, dan kiri, maka jenis keretakan adalah TURTLE.
    result = ImageClass.get_class(ImageProcessor.classify(image))

    # PROSES 10: Response dikirim
    # Setiap gambar hasil Proses sebelumnya, berikut hasil klasifikasi dikirimkan kembali ke pengguna menggunakan JSON.
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80")