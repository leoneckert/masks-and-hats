import sys, os, subprocess, re
def load_masks(the_dir):
    onlyfiles = [f for f in os.listdir(the_dir) if os.path.isfile(os.path.join(the_dir, f)) and (f.endswith("jpg") or f.endswith("png"))]
    fronts = [f for f in onlyfiles if f.split(".")[0].endswith("front") and f.endswith(".png")]
    backs = [f for f in onlyfiles if f.split(".")[0].endswith("back") and f.endswith(".jpg")]
    # make pairs
    masks = dict()
    no_matches = True
    for f in fronts:
        name = "_".join(f.split("_")[:-1])
        for ff in backs:
            name_ = "_".join(ff.split("_")[:-1])
            if name == name_:
                no_matches = False
                masks[name] = {
                        "front": os.path.join( the_dir, f),
                        "back": os.path.join( the_dir, ff)
                        }
    if no_matches == True:
        print "[-] Exiting program"
        print """
        Could not find valid mask pairs in: """ + the_dir + """
        For more information on file naming check the github repo.
        """
        sys.exit()
    return masks
        
        

def run(args):
    # deal with input:
    print "[+] Inspecting input"
    input_paths = list()
    is_video = False
    in_arg = args.input
    img_extensions = set([".jpg", ".jpeg", ".tif", ".png", ".tiff", ".gif"])
    vid_extensions = set([".mp4", ".mov"])
    if os.path.isfile(in_arg):
        ext = "." + in_arg.split(".")[-1]
        if ext in img_extensions:
            input_paths.append(in_arg) 
        elif ext in vid_extensions:
            print "[+] Extracting frames from video."
            print """
            Trying to extract frames from video using ffmpeg. If you
            don't have ffmpeg installed, this will throw some error I did not
            accomodate for in this script :)
            """
            is_video = True
            temp_dir = "temp_0"
            while os.path.isdir(temp_dir):
                temp_dir = temp_dir.split("_")[0] + "_" + str( int(temp_dir.split("_")[-1]  ) +1  )  
            os.mkdir(temp_dir)

            subprocess.call(["ffmpeg",  "-i", in_arg, "-qscale:v", "2", os.path.join(temp_dir, "frame%10d.jpg")])
            # ffmpeg -i input-video.avi -vn -acodec copy output-audio.aac
            subprocess.call(["ffmpeg",  "-i", in_arg, "-vn", "-acodec", "copy", os.path.join(temp_dir, "sound.aac")])
            # get original framerate:
            a = subprocess.Popen(["ffmpeg", "-i", in_arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, out = a.communicate()
            match_dict = re.search(r"\s(?P<fps>[\d\.]+?)\stbr", out).groupdict()
            fps = float(match_dict["fps"])
            writer = open(os.path.join(temp_dir, "fps.txt"), "w")
            writer.write(str(fps))
            writer.close()
            for f in os.listdir(temp_dir):
                if f.endswith(".jpg"):
                    input_paths.append( os.path.join(temp_dir, f) )
            
        else:
            print "[-] Exiting program"
            print """
            Sorry, the extension of you input file is not recognised.
            This doesn't mean your file isn't valid, but that you have to
            change either the file extension or the source code to test it.
            Currently support image extensions: """ + str(list(img_extensions)) + """
            Currently support video extensions: """ + str(list(vid_extensions)) + """
            """
            sys.exit()
    elif os.path.isdir(in_arg):
        for f in os.listdir(in_arg):
            ext = "." + f.split(".")[-1]
            if ext in img_extensions:
                input_paths.append( os.path.join(in_arg, f) )
        if len(input_paths) < 1:
            print "[-] Exiting program"
            print """
            No images found in """ + in_arg + """
            Right now not supporting more than one video at once, can be
            changed in the source code though. 
            """
            sys.exit()
    else:
        print "[-] Exiting program"
        print """
        Cannot find your input: """ + in_arg + """
        """
        sys.exit()
            
    print "[+] Inspecting input: Done."
    
    # deal with masks:
    masks = dict()
    print "[+] Inspecting masks"
    ma_arg = args.mask
    if os.path.isdir(ma_arg):
        masks = load_masks(ma_arg)
    elif os.path.isfile(ma_arg):
        # check if file is valid and correspinding file exists
        f = ma_arg.split("/")[-1]
        f_name = ".".join( f.split(".")[:-1])
        f_ext = "." + f.split(".")[-1]
        if f_ext == ".png":
            
            spec = f_name.split("_")[-1]
            if spec == "front":
                mask_name = "_".join(f_name.split("_")[:-1])
                f_path = "/".join( ma_arg.split("/")[:-1])
                ff = mask_name + "_back.jpg"
                ff_path = os.path.join( f_path, ff)
                if os.path.isfile(ff_path):
                    masks[mask_name] = {
                            "front": ma_arg,
                            "back": ff_path
                            }
                else:
                    print "[-] Exiting program"
                    print """
                    You specified file: """ + ma_arg + """
                    Cannot find corresponding file: """ + ff_path + """
                    """
                    sys.exit()
            else:
                print "[-] Exiting program"
                print """
                The file you specified for the mask seems not be named
                correctly. For more Information check the documentation on my github.
                """
                sys.exit()
        elif f_ext == ".jpg":
            spec = f_name.split("_")[-1]
            if spec == "back":
                mask_name = "_".join(f_name.split("_")[:-1])
                f_path = "/".join( ma_arg.split("/")[:-1])
                ff = mask_name + "_front.png"
                ff_path = os.path.join( f_path, ff)
                if os.path.isfile(ff_path):
                    masks[mask_name] = {
                            "front": ff_path,
                            "back": ma_arg
                            }
                else:
                    print "[-] Exiting program"
                    print """
                    You specified file: """ + ma_arg + """
                    Cannot find correspoding file: """ + ff_path + """
                    """
                    sys.exit()
            else:
                print "[-] Exiting program"
                print """
                The file you specified for the mask seems not be named
                correctly. For more Information check the documentation on my github.
                """
                sys.exit()
        else:
            print "[-] Exiting program"
            print """
            The file you specified for the mask has to be either a .png or
            .jpg. For more Information check the documentation on my github.
            """
            sys.exit()
    else:
        print "[-] Exiting program"
        print """
        Cannot find a masks at: """ + ma_arg + """
        """
        sys.exit()

    print "[+] Inspecting masks: Done."

    # Deal with the outout paths:
    print "[+] Validating output paths"
    output_paths = [] 
    out_arg = args.output
    #check if actual filename is specified:
    potential_ext = "." + out_arg.split(".")[-1] 
    if potential_ext in img_extensions:
        if is_video == True:
            print "[-] Exiting program"
            print """
            The input you specified is a video, the output filename specifies
            an image.
            """
            sys.exit()
        elif len(input_paths) > 1:
            print "[-] Exiting program"
            print """
            You specified multiple input images, but only specified one single
            output filename.
            """
            sys.exit()
        else:
            path = "/".join(out_arg.split("/")[:-1])
            if not os.path.isdir(path) and path != '':
                os.makedirs(path)
            output_paths.append(out_arg)

    elif potential_ext in vid_extensions:
        if is_video == False:
            print "[-] Exiting program"
            print """
            The input you specified is one or more images, the output filename specifies
            a video.
            """
            sys.exit()
        else:
            path = "/".join(out_arg.split("/")[:-1])
            if not os.path.isdir(path) and path != '':
                os.makedirs(path)
            output_paths.append(out_arg)
    else:
        if not os.path.isdir(out_arg) and out_arg != '':
            os.makedirs(out_arg)
        if is_video == False:
            for p in input_paths:
                f = p.split("/")[-1]
                f_name = ".".join( f.split(".")[:-1])
                f_ext = "." + f.split(".")[-1]
                f_out = f_name + "_masked" + f_ext
                out_p = os.path.join(out_arg, f_out)
                output_paths.append(out_p)
        else:
            f = in_arg.split("/")[-1]
            f_name = ".".join( f.split(".")[:-1])
            f_ext = "." + f.split(".")[-1]
            f_out = f_name + "_masked" + f_ext
            out_p = os.path.join(out_arg, f_out)
            output_paths.append(out_p)
    print "[+] Validating output paths: Done."
    return input_paths, masks, output_paths, args.unique, is_video
