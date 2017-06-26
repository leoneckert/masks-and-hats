import random, os
import cv2
import dlib
import numpy as np

# from mask_generator import make_mask


detector = dlib.get_frontal_face_detector()
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(PREDICTOR_PATH)
MASK_DIR = "masks/"


def load_masks():
    onlyfiles = [f for f in os.listdir(MASK_DIR) if os.path.isfile(os.path.join(MASK_DIR, f)) and (f.endswith("jpg") or f.endswith("png"))]
    fronts = [f for f in onlyfiles if f.split(".")[0].endswith("front") and f.endswith(".png")]
    backs = [f for f in onlyfiles if f.split(".")[0].endswith("back") and f.endswith(".jpg")]
    # make pairs
    masks = dict()
    for f in fronts:
        name = f.split("_")[0]
        for ff in backs:
            name_ = ff.split("_")[0]
            if name == name_:
                masks[name] = {
                        "front": f,
                        "back": ff
                        }
    return masks

def get_random_mask(masks):
    names = [m for m in masks]
    ran = random.choice(names)
    return get_img( os.path.join(MASK_DIR, masks[ran]["front"] ), True), get_img(os.path.join(MASK_DIR, masks[ran]["back"] ))

# def show_img_with_rectangle(img, rect):
    # img_with_rect = img.copy()
    # x, y, h, w = rect.left(), rect.top(), rect.width(), rect.height()
    # cv2.rectangle(img_with_rect, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # cv2.imshow("face with rectangle", img_with_rect)
    # cv2.waitKey(0)

# def show_img_with_landmarks(img, landmarks, name="face_with_landmarks"):
    # img_with_landmarks = img.copy()
    # for idx, point in enumerate(landmarks):
        # pos = (point[0, 0], point[0, 1])
        # cv2.circle(img_with_landmarks,pos, 1, (0,0,255), -1)
    # cv2.imshow(name, img_with_landmarks)
    # cv2.waitKey(0)

def add_alpha_channel(img):
    img = cv2.imread(path)
    b_channel, g_channel, r_channel = cv2.split(img)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255 #creating a dummy alpha channel image.
    return cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

def remove_alpha_channel(img):
    return img[:,:,:3]

def get_img(path, mask=False):
    print "[+] Opened image from:", path
    if mask:
        return cv2.imread(path, cv2.IMREAD_UNCHANGED)
    else:
        return cv2.imread(path)

def get_rects(img):
    rects = detector(img)
    print "[+] Number of faces found:", len(rects)
    return rects

def get_landmarks(img, rect):
    return np.matrix([[p.x, p.y] for p in predictor(img, rect).parts()])
# https://matthewearl.github.io/2015/07/28/switching-eds-with-python/

def transformation_from_points(points1, points2):
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
    R = (U * Vt).T

    return np.vstack([np.hstack(((s2 / s1) * R,
                                       c2.T - (s2 / s1) * R * c1.T)),
                         np.matrix([0., 0., 1.])])

def warp_im(im, M, dshape):
    output_im = np.ones(dshape, dtype=im.dtype)*0
    cv2.warpAffine(im,
                   M[:2],
                   (dshape[1], dshape[0]),
                   dst=output_im,
                   borderMode=cv2.BORDER_TRANSPARENT,
                   flags=cv2.WARP_INVERSE_MAP)
    return output_im

def align_mask_img(ldmks, img, mask_ldmks, mask_img):
    transformation_matrix = transformation_from_points(ldmks, mask_ldmks) 
    return warp_im(mask_img, transformation_matrix, img.shape)

def sort_faces_by_size(faces):
    pairs = list()
    for face in faces:
        x = face.left()
        y = face.top()
        w = face.right() - x
        h = face.bottom() - y
        pairs.append([face, w*h])
    pairs.sort(key=lambda x: x[1])
    return [f[0] for f in pairs]

def encrypt_faces(path):
    img = get_img(path)

    # find all faces
    faces = get_rects(img)
    if len(faces) == 0:
        print "no faces found"
        return
    masks = load_masks()
    
    out = img.copy()
    
    #sort faces by size, start with the smallest
    faces = sort_faces_by_size(faces)
    
    # # interate over faces
    
    for i, face in enumerate(faces, 0):
        # pick random mask for face
        mask_front, mask_back = get_random_mask(masks)
        mask_face = get_rects(mask_back)[0]

        # # get landmarks
        img = remove_alpha_channel(img)
        face_ldmks = get_landmarks(img, face)
        mask_ldmks = get_landmarks(mask_back, mask_face)

        # # align mask to face
        img = add_alpha_channel(img) 
        aligned_mask = align_mask_img(face_ldmks, img, mask_ldmks, mask_front)
	
	
        x_offset=y_offset=0
        try:
            for c in range(0,3):
                out[0:out.shape[0],0:out.shape[1], c] =  aligned_mask[:,:,c] * (aligned_mask[:,:,3]/255.0) +  out[0:out.shape[0], 0:out.shape[1], c] * (1.0 - aligned_mask[:,:,3]/255.0)
        except Exception, e:
            print e
            pass
	
    out_path = ".".join(path.split(".")[:-1]) + "_masked." + path.split(".")[-1] 
    cv2.imwrite(out_path, out)
    


        
        




        



if __name__ == "__main__":
    import sys
    path = sys.argv[1]

    encrypt_faces(path)
