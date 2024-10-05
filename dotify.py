from PIL import Image
from numpy import asarray
import numpy as np

import sys
import os

# base var

help_msg = """Usage:
python dotify.py <input_image_path> <dot_size> [--invert] [--black-dots] [--normalize]
                                             [--spread <spread>] [--exposure <exposure>] [...]

Mandatory arguments:
  <input_image_path>: path to input image
  <dot_size>: integer greater than 1 representing the size of a dot in pixel

Options:
  --invert: inverse the original image
  --black-dots: by default the image is white dots on a black background, 
                when this arguments is passed: black dots on a white background

  --normalize: normalize the input image (the brightest pixel will be white and the darkest black)
  --spread <spread>: float the distance between 2 dots (default = 0.5)
  --expossure <expossure>: float the sensitivity to brightness (between 0.1 and 10, default = 2)
  
  -h, --help: display this message"""

  

inverse = False
normalize = False
black_dots = False

ecart = 0.5
exposure = 2



# parse arg
args = sys.argv[1:]

if '-h' in args or '--help' in args:
    print()
    print(help_msg)
    sys.exit(0)


if len(args) < 2:
    print("\n[!!] not enough arguments\n")
    print(help_msg)
    sys.exit(1)

input_image_path = args[0]

try: 
    compression_ratio = int(args[1])
    if compression_ratio <= 1:
        print("\n[!!] dot_size must be greater than 1\n")
        print(help_msg)
        sys.exit(1)

except:
    print("\n[!!] dot_size must be an integer\n")
    print(help_msg)
    sys.exit(1)


idx = 2

while idx < len(args):
    arg = args[idx]
    if '--invert' == arg:
        inverse = True

    elif '--normalize' == arg:
        normalize = True

    elif '--black-dots' == arg:
        black_dots = True

    elif '--spread' == arg:
        try:
            ecart = float(args[idx+1])
            
            idx+=1

        except:
            print("\n[!!] spread must be an float\n")
            print(help_msg)
            sys.exit(1)

    elif '--exposure' == arg:
        try:
            exposure = float(args[idx+1])
            
            if exposure < 0.1 or exposure > 10:
                print("\n[!!] exposure must be between 0.1 and 10\n")
                print(help_msg)
                sys.exit(1)
            idx+=1

        except:
            print("\n[!!] exposure must be an float\n")
            print(help_msg)
            sys.exit(1)


    else:
        print(f"\n[!!] unknown argument: {arg}\n")
        print(help_msg)
        sys.exit(1)

    idx += 1 

compression_ratio += int(ecart)


def compress_img(image, ratio):

    out_shape = image.shape[0]//ratio , image.shape[1]//ratio, image.shape[2]
    out = np.zeros(out_shape)

    for i in range(out_shape[0]):
        for j in range(out_shape[1]):
            if ((j+1)*ratio < image.shape[1] and \
                (i+1)*ratio < image.shape[0]):

                out[i, j] = np.mean(image[i*ratio:(i+1)*ratio, j*ratio:(j+1)*ratio, :], axis=(0, 1))/255
            
            elif ((j+1)*ratio >= image.shape[1]):
                out[i, j] = out[i, j-1]

            elif ((i+1)*ratio >= image.shape[0]):
                out[i, j] = out[i-1, j]
            else:
                out[i, j] = out[i-1, j-1]
    return out


def to_greyscale(image):
    return np.dot(image[...,:3], [0.299, 0.587, 0.114])


def dotify(image, ratio):
    out = np.zeros((image.shape[0]*ratio, image.shape[1]*ratio))

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            x = i*ratio
            y = j*ratio

            value = image[i, j]

            if black_dots:
                value = value**exposure
            else:
                value = value**(1/exposure)

            if value < 0.001:
                value = 0

            radius = ratio/2 * value 
            cx = x+ratio/2
            cy = y+ratio/2

            for k in range(ratio):
                for l in range(ratio):
                        if value == 0:
                            continue

                        distance = np.sqrt((cx-x-k)**2 + (cy-y-l)**2) + ecart
                        
                        if distance+1 < radius:
                            out[x+k, y+l] = 255

                        elif distance < radius:
                            out[x+k, y+l] = 255*(radius - distance)


    return out



# load image
print("\n[loading image]...", end='', flush=True)
try:
    img = Image.open(input_image_path).convert('RGB')
except:
    print(f"\n[!!] cannot open the file `{input_image_path}`\n")
    print(help_msg)
    sys.exit(1)


shape = img.size
img_array = asarray(img)
print("\r[loading image]: OK")

print("[compressing image]...", end='', flush=True)
compressed_img = compress_img(img_array, compression_ratio)
if inverse:
    compressed_img = 1-compressed_img
if normalize:
    compressed_img -= compressed_img.min()
    compressed_img /=  compressed_img.max()

print("\r[compressing image]: OK")

print("[Image to grey scale]...", end='', flush=True)
grey_img = to_greyscale(compressed_img)
print("\r[Image to grey scale]: OK")

print("[Dotifying image]...", end='', flush=True)
if black_dots:
    grey_img = 1 - grey_img

dotify_img = dotify(grey_img, compression_ratio) 

if black_dots:
    dotify_img = 255 - dotify_img


print("\r[Dotifying image]: OK")


# save image
print(f"\r[Saving new image]: ...", end='', flush=True)
img = Image.fromarray(dotify_img.astype('uint8'))

# remove ext
splited =  input_image_path.split('.')
input_image_path = '.'.join(splited[:-1])

# gen name
out_path = input_image_path+'_dotifyed.png'
i = 1
while os.path.isfile(out_path):
    out_path = input_image_path+f"_dotifyed_{i}.png"
    i += 1

img.save(out_path, 'png')
print(f"\r[Saving new image: ({out_path}) ]: OK")