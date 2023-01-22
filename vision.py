import cv2
import numpy as np


def scan_image(filepath: str, white_text: bool = False):
    img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)

    if not white_text:
        img = cv2.bitwise_not(img)

    blurred = cv2.GaussianBlur(img, (3, 3), 1, 1)
    thinned = cv2.ximgproc.thinning(blurred, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    #canny = cv2.Canny(thinned, 0, 255)
    cv2.imshow("img", thinned)

    contours, _ = cv2.findContours(thinned, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

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
        xs[i] = x
        ys[i] = y

    min_x = np.min(xs)
    min_y = np.min(ys)
    max_x = np.max(xs)
    max_y = np.max(ys)

    xs -= min_x
    ys -= min_y

    xs /= max_x - min_x
    ys /= max_y - min_y

    xs /= 2.0
    ys /= 2.0

    xs += 0.25
    ys += 0.25

    min_x = np.min(xs)
    min_y = np.min(ys)
    max_x = np.max(xs)
    max_y = np.max(ys)

    print("min: "+str((min_x, min_y)))
    print("max: "+str((max_x, max_y)))

    return xs, ys
