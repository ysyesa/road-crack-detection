# FILE: constants.py

# Kelas Pixel berisi atribut warna piksel untuk gambar binary.
# Piksel dengan nilai 0 berwarna hitam, sedangkan piksel dengan nilai 255 berwarna putih.
class Pixel:
    WANTED = 0
    UNWANTED = 255

# Kelas ImageClass berisi jenis-jenis keretakan.
# Nilai pada variabel-variabel ini sebenarnya bebas.
class ImageClass:
    LONGITUDINAL_CRACK = 0
    TRAVERSAL_CRACK = 1
    TURTLE_CRACK = 2

    @staticmethod
    def get_class(code):
        if code == 0:
            return "longitudinal"
        elif code == 1:
            return "traversal"
        else:
            return "turtle"
