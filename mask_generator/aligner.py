"""
Align face and image sizes
"""
from __future__ import division
import cv2
import numpy as np

MOUTH_POINTS = list(range(59, 77))
RIGHT_BROW_POINTS = list(range(17, 22))
LEFT_BROW_POINTS = list(range(22, 27))
RIGHT_EYE_POINTS = list(range(30, 38))
LEFT_EYE_POINTS = list(range(39, 48))
NOSE_POINTS = list(range(49, 59))
BORDER_POINTS = list(range(0, 16))
ALIGN_POINTS = (LEFT_BROW_POINTS + RIGHT_EYE_POINTS + LEFT_EYE_POINTS +
                               RIGHT_BROW_POINTS + NOSE_POINTS + MOUTH_POINTS)

#ALIGN_POINTS = (RIGHT_EYE_POINTS + LEFT_EYE_POINTS + BORDER_POINTS)

def transformation_from_points(points1, points2):
    """
    Return an affine transformation [s * R | T] such that:
        sum ||s*R*p1,i + T - p2,i||^2
    is minimized.
    """
    # Solve the procrustes problem by subtracting centroids, scaling by the
    # standard deviation, and then using the SVD to calculate the rotation. See
    # the following for more details:
    #   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem

    points1 = points1.astype(np.float64)
    points2 = points2.astype(np.float64)

    c1 = np.mean(points1, axis=0)
    c2 = np.mean(points2, axis=0)
    points1 -= c1
    points2 -= c2

    s1 = np.std(points1)
    s2 = np.std(points2)
    points1 /= s1
    points2 /= s2

    U, S, Vt = np.linalg.svd(points1.T * points2)

    # The R we seek is in fact the transpose of the one given by U * Vt. This
    # is because the above formulation assumes the matrix goes on the right
    # (with row vectors) where as our solution requires the matrix to be on the
    # left (with column vectors).
    R = (U * Vt).T

    return np.vstack([np.hstack(((s2 / s1) * R,
                                       c2.T - (s2 / s1) * R * c1.T)),
                         np.matrix([0., 0., 1.])])


def warp_im(im, M, dshape):
    output_im = np.zeros(dshape, dtype=im.dtype)
    cv2.warpAffine(im,
                   M[:2],
                   (dshape[1], dshape[0]),
                   dst=output_im,
                   borderMode=cv2.BORDER_TRANSPARENT,
                   flags=cv2.WARP_INVERSE_MAP)
    return output_im


def align(im1, im2, landmarks1, landmarks2):
    landmarks1 = np.matrix([[p[0], p[1]] for p in landmarks1])
    landmarks2 = np.matrix([[p[0], p[1]] for p in landmarks2])
    M = transformation_from_points(landmarks1[ALIGN_POINTS], landmarks2[ALIGN_POINTS])
    #M = transformation_from_points(landmarks1, landmarks2)
    aligned_im = warp_im(im2, M, im1.shape)
    return aligned_im

def positive_cap(num):
  """ Cap a number to ensure positivity

  :param num: positive or negative number
  :returns: (overflow, capped_number)
  """
  if num < 0:
    return 0, abs(num)
  else:
    return num, 0

def roi_coordinates(rect, size, scale):
  """ Align the rectangle into the center and return the top-left coordinates
  within the new size. If rect is smaller, we add borders.

  :param rect: (x, y, w, h) bounding rectangle of the face
  :param size: (width, height) are the desired dimensions
  :param scale: scaling factor of the rectangle to be resized
  :returns: 4 numbers. Top-left coordinates of the aligned ROI.
    (x, y, border_x, border_y). All values are > 0.
  """
  rectx, recty, rectw, recth = rect
  new_height, new_width = size
  mid_x = int((rectx + rectw/2) * scale)
  mid_y = int((recty + recth/2) * scale)
  roi_x = mid_x - int(new_width/2)
  roi_y = mid_y - int(new_height/2)

  roi_x, border_x = positive_cap(roi_x)
  roi_y, border_y = positive_cap(roi_y)
  return roi_x, roi_y, border_x, border_y

def scaling_factor(rect, size):
  """ Calculate the scaling factor for the current image to be
      resized to the new dimensions

  :param rect: (x, y, w, h) bounding rectangle of the face
  :param size: (width, height) are the desired dimensions
  :returns: floating point scaling factor
  """
  new_height, new_width = size
  rect_h, rect_w = rect[2:]
  height_ratio = rect_h / new_height
  width_ratio = rect_w / new_width
  scale = 1
  if height_ratio > width_ratio:
    new_recth = 0.8 * new_height
    scale = new_recth / rect_h
  else:
    new_rectw = 0.8 * new_width
    scale = new_rectw / rect_w
  return scale

def resize_image(img, scale):
  """ Resize image with the provided scaling factor

  :param img: image to be resized
  :param scale: scaling factor for resizing the image
  """
  cur_height, cur_width = img.shape[:2]
  new_scaled_height = int(scale * cur_height)
  new_scaled_width = int(scale * cur_width)

  return cv2.resize(img, (new_scaled_width, new_scaled_height))

def resize_align(img, points, size):
  """ Resize image and associated points, align face to the center
    and crop to the desired size

  :param img: image to be resized
  :param points: *m* x 2 array of points
  :param size: (height, width) tuple of new desired size
  """
  new_height, new_width = size

  # Resize image based on bounding rectangle
  rect = cv2.boundingRect(np.array([points], np.int32))
  scale = scaling_factor(rect, size)
  img = resize_image(img, scale)

  # Align bounding rect to center
  cur_height, cur_width = img.shape[:2]
  roi_x, roi_y, border_x, border_y = roi_coordinates(rect, size, scale)
  roi_h = np.min([new_height-border_y, cur_height-roi_y])
  roi_w = np.min([new_width-border_x, cur_width-roi_x])

  # Crop to supplied size
  crop = np.zeros((new_height, new_width, 3), img.dtype)
  crop[border_y:border_y+roi_h, border_x:border_x+roi_w] = (
     img[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w])

  # Scale and align face points to the crop
  points[:, 0] = (points[:, 0] * scale) + (border_x - roi_x)
  points[:, 1] = (points[:, 1] * scale) + (border_y - roi_y)

  return (crop, points)
