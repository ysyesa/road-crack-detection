class Pixel:
    WANTED = 0
    UNWANTED = 255

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
