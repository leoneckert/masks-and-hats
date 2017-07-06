import os
def run(args):
    # deal with input 
    print "[+] Inspecting input"
    input_paths = list()
    in_arg = args.input
    img_extensions = set([".jpg", ".jpeg", ".tif", ".png", ".tiff", ".gif"])
    if os.path.isfile(in_arg):
        ext = "." + in_arg.split(".")[-1]
        if ext in img_extensions:
            input_paths.append(in_arg) 
        else:
            print "[-] Exiting program"
            print """
            Sorry, the extension of you input file is not recognised.
            This doesn't mean your file isn't valid, but that you have to
            change either the file extension or the source code to test it.
            Currently support image extensions: """ + str(list(img_extensions)) + """
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
    
    # deal with output path
    print "[+] Preparing output paths"
    output_info = dict() 
    out_arg = args.output

    if os.path.isfile(out_arg):
        print "[-] Exiting program"
        print """
        Your output path is a file that already exists: """ + in_arg + """
        It should be a directory that either already exists or not, 
        but in no case a filename. This is beacuse this script actually 
        creates two files for each mask. If you want to give them a name,
        use the '-n' flag.
        """
        sys.exit()
    else:
        if not os.path.isdir(out_arg):
            os.makedirs(out_arg)
          
        output_info["base"] = out_arg
        output_info["name"] = args.name
    
    print "[+] Preparing output paths. Done."
    return input_paths, output_info




