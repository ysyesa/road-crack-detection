from constants import Pixel, ImageClass
from collections import deque

class ImageProcessor:
    @staticmethod
    def get_binary_image(_image, _threshold):
        height, width = _image.shape[0], _image.shape[1]
        for i in range(height):
            for j in range(width):
                if _image[i][j] < _threshold:
                    _image[i][j] = Pixel.WANTED
                else:
                    _image[i][j] = Pixel.UNWANTED
        return _image

    @staticmethod
    def get_wanted_regions(_image):
        height, width = _image.shape[0], _image.shape[1]

        def is_wanted_pixel(_y, _x):
            return _image[_y][_x] == Pixel.WANTED

        def move0(_y, _x):
            return _y, _x + 1

        def move45(_y, _x):
            return _y - 1, _x + 1

        def move90(_y, _x):
            return _y - 1, _x

        def move135(_y, _x):
            return _y - 1, _x - 1

        def move180(_y, _x):
            return _y, _x - 1

        def move225(_y, _x):
            return _y + 1, _x - 1

        def move270(_y, _x):
            return _y + 1, _x

        def move315(_y, _x):
            return _y + 1, _x + 1

        pixel_visits = [[0 for j in range(width)] for i in range(height)]

        def is_pixel_visited(_y, _x):
            return pixel_visits[_y][_x] == 1

        def visit_pixel(_y, _x):
            pixel_visits[_y][_x] = 1

        def is_pixel_outside_image(_y, _x):
            return _y < 0 or _y >= height or _x < 0 or _x >= width

        regions = []
        for i in range(height):
            for j in range(width):
                if is_wanted_pixel(i, j):
                    region = []
                    must_visit_pixels = deque([(i, j)])
                    while len(must_visit_pixels) > 0:
                        pixel = must_visit_pixels.popleft()
                        y, x = pixel[0], pixel[1]
                        if is_pixel_visited(y, x):
                            continue
                        visit_pixel(y, x)
                        region.append((y, x))
                        funcs_to_move = [move0, move45, move90, move135, move180, move225, move270, move315]
                        for func in funcs_to_move:
                            neighbor_y, neighbor_x = func(y, x)
                            if not is_pixel_outside_image(neighbor_y, neighbor_x) and is_wanted_pixel(neighbor_y,
                                                                                                      neighbor_x):
                                must_visit_pixels.append((neighbor_y, neighbor_x))
                    if len(region) > 0:
                        regions.append(region)
        return regions

    @staticmethod
    def classify(_image):
        # Find image bounds with coefficient
        height, width = _image.shape[0], _image.shape[1]
        coefficient = 0.1
        bound_left = int(coefficient * width)
        bound_right = int(width - (coefficient * width))
        bound_upper = int(coefficient * height)
        bound_lower = int(height - (coefficient * height))

        # Find wanted area in upper part of image
        wanted_pixel_total = 0
        for i in range(bound_upper):
            for j in range(width):
                if _image[i][j] == 0:
                    wanted_pixel_total = wanted_pixel_total + 1
        wanted_area_upper = wanted_pixel_total / (bound_upper * width)

        # Find wanted area in lower part of image
        wanted_pixel_total = 0
        for i in range(bound_lower, height):
            for j in range(width):
                if _image[i][j] == 0:
                    wanted_pixel_total = wanted_pixel_total + 1
        wanted_area_lower = wanted_pixel_total / ((height - bound_lower) * width)

        # Find wanted area in left part of image
        wanted_pixel_total = 0
        for i in range(height):
            for j in range(bound_left):
                if _image[i][j] == 0:
                    wanted_pixel_total = wanted_pixel_total + 1
        wanted_area_left = wanted_pixel_total / (bound_left * height)

        # Find wanted area in right part of image
        wanted_pixel_total = 0
        for i in range(height):
            for j in range(bound_right, width):
                if _image[i][j] == 0:
                    wanted_pixel_total = wanted_pixel_total + 1
        wanted_area_right = wanted_pixel_total / ((width - bound_right) * height)

        # Classify based on wanted area
        if wanted_area_upper > 0 and wanted_area_lower > 0 and wanted_area_left > 0 and wanted_area_right > 0:
            return ImageClass.TURTLE_CRACK
        elif wanted_area_upper > 0 and wanted_area_lower > 0 and wanted_area_left == 0 and wanted_area_right == 0:
            return ImageClass.LONGITUDINAL_CRACK
        else:
            return ImageClass.TRAVERSAL_CRACK

if __name__ == "__main__":
    import cv2
    import numpy as np
    image = cv2.imread("res/crack1.png")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.erode(image, np.ones((20, 20), np.int))
    image = ImageProcessor.get_binary_image(_image=image, _threshold=128)
    regions = ImageProcessor.get_wanted_regions(image)
    image = ImageProcessor.get_binary_image(_image=image, _threshold=0)
    height, width = image.shape[0], image.shape[1]
    total_area = height * width
    percent = 10000 / total_area * 100
    print(total_area, percent)
    for region in regions:
        if len(region) >= 10000:
            for pixel in region:
                y, x = pixel[0], pixel[1]
                image[y][x] = 0
    cv2.imshow("Window 1", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
