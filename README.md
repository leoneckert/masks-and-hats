# Masks and Hats

## Intro
This is a toolkit for making silly (or not silly) masks and hats and put them on people's faces. All digitally. There is two scripts, `create_mask.py` and `apply_mask.py`. 
<br>Be aware, the aesthetic this script is designed to produce is the one known from hand drawn ‘mustache and glasses’ or from old lo-fi paper masks. If you are looking for a more faceswap-style-effect this is not what you want. 
<br><br>Below is the [logic of the script](#logic-behind-this-script) explained, some [Usage Guidelines]() and some [help for installing the dependencies](): OpenCV, dlib and Stasm (as tested on OSX). 
<br><br>**Thanks** to [Sam Lavigne](https://github.com/antiboredom) on whose code the `create_mask.py` entirely relies. [His repo](https://github.com/antiboredom/mask-generator) is found slightly modified in the mask_generator directory of this project. 
<br>The foundation of the other script, `apply_mask.py` is [this tutorial](http://www.learnopencv.com/face-morph-using-opencv-cpp-python/). 
<br><br>Please also check out [previous explorations](http://leoneckert.com/projects/anonymizme/) of mine in which I mainly had fun with replacing faces with *visually similar* ones as retrieved from search engines in real time. 

![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/mask.gif)

## Usage Guidelines
After having all the dependencies installed, you can try running some test commands. I provided some photos of random people and example masks to play with. Every command can be run with the `-h` flag as well to show the options. 

### Drawn masks and hats

<br>Let’s start with a classic:

```
$ python apply_mask.py -i examples/faces -m examples/masks -o examples/masked
```

`-i examples/faces` means we apply masks to all the faces found on all the images in the examples/faces directory.<br>
` -m examples/masks` defines where to look for masks to apply and<br>
`-o examples/masked` where to save the output the output. 

After running this command, you will hopefully find something like this:
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/output_01.jpg)


<br>Now let’s put hats, hats are always fun and I drew one for you:

```
python apply_mask.py -i examples/groups/group1.jpg -m examples/hats -o examples/masked/group_w_hats.jpg 
```

Same idea, the output looks hopefully like this:
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/output_02.jpg)








### Logic behind this script
Here is three simple steps to *morph* one face onto another.

1) Detect faces.
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-01.png)
2) Calculate a Transformation matrix describing the difference. 
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-02.png)
3) Transform one face using the transformation matrix to fit onto the other.
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-03.png)

Obviously, (silly) masks should look whatever they want, not necessarily face-like. That’s why **this script works with mask files consisting of two images**: a ‘back’ (.jpg) image with a reference face and a ‘front’ (transparent .png) image with the mask.
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-04.png)

The idea then is to use the reference image to calculate whatever transformation matrix is needed for a given destination face, but to use it to morph the mask instead. 
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-05.png)
![](https://raw.githubusercontent.com/leoneckert/masks-and-hats/master/imgs/img-06.png)


That way, masks don’t have to resemble faces or be of any specific size (for bigger masks, just add margin to the reference image, and draw whatever you feel like onto the mask png). 





