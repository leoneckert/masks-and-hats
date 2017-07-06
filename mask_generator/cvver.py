import cv2

def is_cv2():
  return cv2.__version__.startswith('2.')

def is_cv3():
  return cv2.__version__.startswith('3.')

def major():
  # this used to be
  # (major, minor, _) = cv2.__version__.split('.')
  # but gave me and error that there are 
  # "too many values to unpack" - potentially this 
  # is different on different machines.....
  (major, minor, _, _) = cv2.__version__.split('.')
  return major
