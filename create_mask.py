import os, sys
import cv2
import dlib
import numpy as np

from tools import validate_create_mask_input
from mask_generator import make_mask

detector = dlib.get_frontal_face_detector()
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(PREDICTOR_PATH)

def add_margin_to_image(img, factor=1):
    w, h, a = img.shape
    leftright_margin = int(w*factor)
    topbottom_margin = int(h*factor)
    canvas = np.ones((w + ( 2 *  leftright_margin ) , h + ( 2 *  topbottom_margin ), a), dtype=img.dtype)*255
    canvas[leftright_margin:leftright_margin+w, topbottom_margin:topbottom_margin+h] = img
    return canvas


def get_img(path):
    print "[+] Opened image from:", path
    return cv2.imread(path)

def get_rects(img):
    rects = detector(img)
    print "\t[+] Number of faces found:", len(rects)
    return rects

def assert_dir(dir_path):
    potential_out_dir = dir_path
    idx = -1
    while os.path.isdir(potential_out_dir):
        idx += 1
        if idx == 0:
            potential_out_dir += "_0"
            continue
        potential_out_dir = "_".join( potential_out_dir.split("_")[:-1] ) +  "_" + str(idx)  
    out_dir = potential_out_dir
    os.mkdir(out_dir)
    print "[+] Created " + out_dir + ". and will save output to that directory" 
    return out_dir

def cut_face_with_margin(img, rect, margin_factor=0):
    x, y, h, w = rect.left(), rect.top(), rect.width(), rect.height()
    x = int(x - margin_factor*w)
    y = int(y - margin_factor*h)
    w = int(w + 2*(margin_factor*w))
    h = int(h + 2*(margin_factor*h))
    return img[y:y+h,x:x+w]

def make_masks(input_paths, output_info): 
    print "[+] Creating masks"
    # for each image, get all faces
    mask_count = 0
    for img_path in input_paths:
        img = get_img(img_path)
        img = add_margin_to_image(img, factor=0.5)

        # find all faces
        faces = get_rects(img)
        if len(faces) == 0:
            print "no faces found"
            return
        
        output_paths = list()
        if len(faces) == 1 and len(input_paths) == 1:
            temp = dict()
            if output_info["name"] != None:
                temp["front"] =  os.path.join(output_info["base"], output_info["name"]) + "_front.png"
                temp["back"] =  os.path.join(output_info["base"], output_info["name"]) + "_back.jpg"
            else:
                p = img_path
                f = p.split("/")[-1]
                name = ".".join( f.split(".")[:-1] )
                temp["front"] =  os.path.join(output_info["base"], name) + "_mask_front.png"
                temp["back"] =  os.path.join(output_info["base"], name) + "_mask_back.jpg"
            output_paths.append(temp)
        
        elif output_info["name"] == None:
            p = img_path
            f = p.split("/")[-1]
            name = ".".join( f.split(".")[:-1] )
            if len(faces) > 1:
                for i in range(len(faces)):
                    temp = dict()
                    temp["front"] =  os.path.join(output_info["base"], name) + "_mask_" + str(i) + "_front.png"
                    temp["back"] =  os.path.join(output_info["base"], name) + "_mask_" + str(i) + "_back.jpg"
                    output_paths.append(temp)
            else:
                temp = dict()
                temp["front"] =  os.path.join(output_info["base"], name) + "_mask_front.png"
                temp["back"] =  os.path.join(output_info["base"], name) + "_mask_back.jpg"
                output_paths.append(temp)
        else: 
            for i in range(len(faces)):
                temp = dict()
                temp["front"] =  os.path.join(output_info["base"], output_info["name"]) + "_" + str(mask_count) + "_front.png"
                temp["back"] =  os.path.join(output_info["base"], output_info["name"]) + "_" + str(mask_count) + "_back.jpg"
                output_paths.append(temp)
                mask_count += 1


        for i, face in enumerate(faces, 0):
            try:
                face_img = cut_face_with_margin(img, face, margin_factor=0.25)
                mask = make_mask.make_mask(face_img)

                if str(type(mask)) != "<type 'numpy.ndarray'>":
                    print "\t\t[-] Trouble with finding a mask for face", str(i), "unfortunately"
                    print "\t\t\tFYI, this is because I am using two different face detection algorithms....." 
                else:
                    cv2.imwrite( output_paths[i]["back"], face_img)
                    cv2.imwrite( output_paths[i]["front"], mask)
                    print "\t\t[+] Saved mask files for face", str(i) 
            except Exception, e:
                print "error with image:", img_path, "\nerror:", e
                pass
        

    print "\n\n[+] Saved new masks to:", output_info["base"]    





if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="This script is to create two mask files to be used with the other scipt named 'apply_mask.py'. ") 
    parser.add_argument("-i", "--input", required=True, type=str, help="image or directory of images in which faces should be found and turned into masks.")
    parser.add_argument("-n", "--name",  type=str, help="name for output mask file")
    # parser.add_argument("-u", "--unique", action="store_true", help="use each mask just once per image/frame. OFF by default")
    parser.add_argument("-o", "--output", required=True, type=str, help="directory where to store the output mask files")
    args = parser.parse_args()
    
    input_paths, output_info = validate_create_mask_input.run(args)
    print "input_paths", input_paths
    print "output_info", output_info

    make_masks(input_paths, output_info)

