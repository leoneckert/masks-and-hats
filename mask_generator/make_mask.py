import sys
import locator
import numpy as np
import cv2
import subprocess
import os


RIGHT_EYE_POINTS = list(range(30, 38))
LEFT_EYE_POINTS = list(range(39, 48))

# leon change: made some changes here to 
# accept the image straight fro the 
# other script rather than the path
def load_image_points(img):
    # img = cv2.imread(path)
    points = locator.face_points(img)
    if len(points) == 0:
        # print('No face in the image')
        return (None, None)
    else:
        return (img, points)


def fill(img, points):
    filler = cv2.convexHull(points)
    cv2.fillConvexPoly(img, filler, 255)

    return img


def drawlines(img, points):
    filler = cv2.convexHull(points)
    cv2.polylines(img, filler, True, (0, 0, 0), thickness=2)
    return img


def mask_from_points(size, points):
    mask = np.zeros(size, np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(points), 255)
    return mask


def alpha_image(img, points, blur=0, dilate=0):
    mask = mask_from_points(img.shape[:2], points)

    if dilate > 0:
        kernel = np.ones((dilate, vdilate), np.uint8)
        mask = cv2.dilate(mask, kernel)

    if blur > 0:
        mask = cv2.blur(mask, (blur, blur))

    return np.dstack((img, mask))


def make_mask(path):
    # original_name = path.split('/')[-1]

    img, points = load_image_points(path)
    if img is None:
        return None

    # if not os.path.exists('eyes'):
        # os.makedirs('eyes')

    # if not os.path.exists('masks'):
        # os.makedirs('masks')

    masked = alpha_image(img, points, 1)
    masked = fill(masked, points[LEFT_EYE_POINTS])
    masked = fill(masked, points[RIGHT_EYE_POINTS])


    # leon change:
    return masked
    #
    # mask_path = 'masks/{}.mask.png'.format(original_name)
    # cv2.imwrite(mask_path, masked)

    # args = ['convert', mask_path, '-trim', '+repage', '-resize', '830x830', '-gravity', 'center', '-background', 'transparent',  '-extent', '850x1100', mask_path + '.tmp.png']
    # subprocess.call(args)
    # args = ['convert', mask_path+'.tmp.png', '-bordercolor', 'none', '-border', '2', '-background', 'black', '-alpha', 'background', '-channel', 'A', '-blur', '3x3', '-level', '0,01%', mask_path+'.tmp2.png']
    # subprocess.call(args)
    # args = ['convert', 'bg.png', mask_path+'.tmp2.png', '-gravity', 'center', '-composite', '-matte', mask_path]
    # subprocess.call(args)

    # os.remove(mask_path+'.tmp.png')
    # os.remove(mask_path+'.tmp2.png')

    # left_eye_path = 'eyes/{}.left.png'.format(original_name)
    # left_eye = alpha_image(img, points[LEFT_EYE_POINTS], dilate=5, blur=1)
    # cv2.imwrite(left_eye_path, left_eye)
    # subprocess.call(['mogrify', '-trim', '+repage', left_eye_path])

    # right_eye_path = 'eyes/{}.right.png'.format(original_name)
    # right_eye = alpha_image(img, points[RIGHT_EYE_POINTS], dilate=5, blur=1)
    # cv2.imwrite(right_eye_path, right_eye)
    # subprocess.call(['mogrify', '-trim', '+repage', right_eye_path])


def test():
    path = 'images/5178124.jpg'
    make_mask(path)


if __name__ == '__main__':
    for path in sys.argv[1:]:
        make_mask(path)
