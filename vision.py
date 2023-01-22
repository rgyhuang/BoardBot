import cv2
import numpy
import numpy as np

display_width = 640
display_height = 480


def scan_image(filepath: str, white_text: bool = False):
    img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)

    if not white_text:
        img = cv2.bitwise_not(img)

    blurred = cv2.GaussianBlur(img, (3, 3), 1, 1)
    thinned = cv2.ximgproc.thinning(blurred, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)

    (height, width) = thinned.shape[:2]
    if width > height:
        scale_ratio = float(display_height) / height
        display_image = cv2.resize(thinned, (int(scale_ratio * width), display_height),
                                   interpolation=cv2.INTER_AREA)
    else:
        scale_ratio = float(display_width) / width
        display_image = cv2.resize(thinned, (display_width, int(scale_ratio * height)),
                                   interpolation=cv2.INTER_AREA)

    cv2.imshow("img", display_image)

    contours, _ = cv2.findContours(thinned, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    word_contour = None
    for contour in contours:
        if word_contour is None or cv2.arcLength(contour, False) > cv2.arcLength(word_contour, False):
            word_contour = contour

    if word_contour is None:
        return None, None

    contour_len = len(word_contour)

    xs = np.empty(contour_len)
    ys = np.empty(contour_len)
    for i in range(contour_len):
        x, y = word_contour[i][0]
        xs[i] = float(x)
        ys[i] = float(y)

    xs = numpy.array(xs)
    ys = numpy.array(ys)

    min_x = np.min(xs)
    min_y = np.min(ys)
    max_x = np.max(xs)
    max_y = np.max(ys)

    xs -= min_x
    ys -= min_y

    scale = max(max_x - min_x, max_y - min_y)

    xs /= float(scale)
    ys /= float(scale)

    xs /= 2.0
    ys /= 2.0

    xs += 0.25
    ys += 0.25

    return xs, ys
