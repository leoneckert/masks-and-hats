import random, os, sys, subprocess, time, shutil
import cv2
import dlib
import numpy as np

# from mask_generator import make_mask


detector = dlib.get_frontal_face_detector()
PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(PREDICTOR_PATH)



def get_random_mask(masks, not_used, unique):
    # someone wants to explain random seed to me?
    # tried various weird things like random.seed(int(time.time()))
    # here without real success
    # problem is when going through a folder of images
    # the first mask will often (?) be the same
    # or is it just me ????????
    chosen = ""
    names = [m for m in masks]
    not_used_names = [m for m in not_used]
    if unique == True:
        if len(not_used_names) == 0:
            front = None
            back = None
            chosen = None
            # print "used all masks"
        else:
            ran = random.choice(not_used_names)
            front = get_img(  masks[ran]["front"] , mask=True )
            back = get_img(  masks[ran]["back"] )
            not_used.pop(ran, None)  
            chosen = ran
    else:
        ran = random.choice(names)
        front = get_img(  masks[ran]["front"] , mask=True )
        back = get_img(  masks[ran]["back"] )
        chosen = ran
    return chosen, front, back, not_used
    
def add_alpha_channel(img):
    # img = cv2.imread(path)
    b_channel, g_channel, r_channel = cv2.split(img)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255 #creating a dummy alpha channel image.
    return cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

def remove_alpha_channel(img):
    return img[:,:,:3]

def get_img(path, mask=False):
    if mask:
        return cv2.imread(path, cv2.IMREAD_UNCHANGED)
    else:
        return cv2.imread(path)

def get_rects(img):
    rects = detector(img)
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

def apply_masks(input_paths, masks, output_paths, apply_unique_masks, is_video):
            
    print "[+] Applying mask(s)" 
    for j, path in enumerate(input_paths, 0):
        print "\n\t[+] Opening", path
        img = get_img(path)
    
        # find all faces
        faces = get_rects(img)
        if len(faces) == 0:
            print "\t[-] no faces found"
            if is_video == True:
                temp_dir = "/".join( path.split("/")[:-1]) 
                f = path.split("/")[-1]
                temp_out = temp_dir + "_masked"
                if not os.path.isdir(temp_out):
                    os.mkdir(temp_out)
                output_path = os.path.join( temp_out, f) 
                print "\t[+] Saving as", output_path
                cv2.imwrite(output_path, img)
            continue
        print "\t[+] Found", len(faces), "faces"
        out = img.copy()

        #sort faces by size, start with the smallest
        faces = sort_faces_by_size(faces)
        
        masks_not_used = masks.copy()
        for i, face in enumerate(faces, 0):
            print "\t\t[face " + str(i+1) + "]", 
            # pick a random mask, check if unique mask was selected 
            mask_name, mask_front, mask_back, masks_not_used = get_random_mask(masks, masks_not_used, apply_unique_masks)
            if mask_name == None:
                print "already used all masks once (you specified '-u' unique mask use)"
                continue
            
            print "picked mask", mask_name
            mask_face = get_rects(mask_back)[0]

            #get landmarks
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
        
        if not is_video:
            print "\t[+] Saving as", output_paths[j] 
            cv2.imwrite(output_paths[j], out)
        else:
            temp_dir = "/".join( path.split("/")[:-1]) 
            f = path.split("/")[-1]
            temp_out = temp_dir + "_masked"
            if not os.path.isdir(temp_out):
                os.mkdir(temp_out)
            output_path = os.path.join( temp_out, f) 
            print "\t[+] Saving as", output_path
            cv2.imwrite(output_path, out)
        
    if is_video == True:
        temp_dir = "/".join( path.split("/")[:-1]) 
        f = path.split("/")[-1]
        temp_out = temp_dir + "_masked"
        
        print "[+] Combining frames to video"
        print """
        This uses ffmpeg, which you hopefully have installed.
        Also not sound supported yet.... would be a few changes in the ffmpeg commands,
        but I thought it was fine for now.
        """
        fps = '25'
        if os.path.isfile( os.path.join(temp_dir, "fps.txt")):
            fps = open( os.path.join( temp_dir, "fps.txt")).read().strip()
        
        subprocess.call(["ffmpeg", "-r", fps,  "-f", "image2", "-i",  os.path.join(temp_out, "frame%10d.jpg"), "-r", fps, os.path.join(temp_out, "video.mp4")  ])
            
        if os.path.isfile( os.path.join(temp_dir, "sound.aac")):
            
            subprocess.call(["ffmpeg",  "-i", os.path.join(temp_out,"video.mp4"), "-i",  os.path.join(temp_dir, "sound.aac"), "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", "-r", fps, output_paths[0]  ])
        else:
            shutil.move( os.path.join(temp_out, "video.mp4"), output_paths[0])
        print "\t[+] Cleaning up after myself"
        
        shutil.rmtree(temp_dir)
        shutil.rmtree(temp_out)
        print "\t[+] Saving as", output_paths[0]




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="This is a script to apply silly masks to faces found in images. Are you sure you want this? If yes, please enjoy.") 
    parser.add_argument("-i", "--input", required=True, type=str, help="path to image, video or folder of images")
    parser.add_argument("-m", "--mask", required=True, type=str, help="path to folder of mask files or indivual mask file (front or back)")
    parser.add_argument("-u", "--unique", action="store_true", help="use each mask just once per image/frame. OFF by default")
    parser.add_argument("-o", "--output", required=True, type=str, help="path to directory or specify filename with .jpg/.png/.mp4/.mov extension.")
    args = parser.parse_args()

    from tools import validate_inputs
    input_paths, masks, output_paths, apply_unique_masks, is_video =  validate_inputs.run(args)
    
    apply_masks(input_paths, masks, output_paths, apply_unique_masks, is_video)
