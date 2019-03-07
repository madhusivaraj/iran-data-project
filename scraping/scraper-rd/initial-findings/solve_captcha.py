import numpy as np
from PIL import Image, ImageFont, ImageDraw
import pytesseract

def solve_captcha(im):
    return ocr_digits(simplify_captcha(im))

def ocr_digits(im):
    s = pytesseract.image_to_string(im, config='digits')
    return ''.join(filter(str.isdigit, s))

def simplify_captcha(im):
    return Image.fromarray(polarize(blur(remove_background(np.array(im)), radius=2)))

BACKGROUND_THRESHOLD = 700

def remove_background(arr, threshold=BACKGROUND_THRESHOLD):
    nrows = arr.shape[0] // 6
    total_threshold = nrows * threshold
    keep = []
    for x in range(arr.shape[1]):
        total = 0
        for y in range(nrows):
            total += sum(arr[y,x])
        if total > total_threshold:
            keep.append(x)
    return arr[:, keep, :]

def blur(arr, radius=1):
    new = np.zeros(arr.shape, dtype=np.uint8)
    for row in range(arr.shape[0]):
        for col in range(arr.shape[1]):
            for color in range(arr.shape[2]):
                total = 0
                n = 0
                for row_off in range(0 - radius, 1 + radius):
                    for col_off in (-1, 0, 1):
                        row_ = row + row_off
                        col_ = col + col_off
                        if row_ >= 0 and row_ < arr.shape[0]:
                            if col_ >= 0 and col_ < arr.shape[1]:
                                total += arr[row_,col_,color]
                                n += 1
                new[row,col,color] = total // n
    return new

def polarize(arr):
    total = 0
    n = 0
    for row in arr:
        for pixel in row:
            s = sum(pixel)
            if s < 255*3:
                total += s
                n += 1
    avg = total / n # average R+G+B of non-white pixels
    new = np.zeros(arr.shape[:2], dtype=np.uint8)
    for y in range(arr.shape[0]):
        for x in range(arr.shape[1]):
            if arr[y,x].sum() > avg:
                new[y,x] = 255
    return new

# Create image showing the steps towards the solution of captcha 'im'
def demo(im):

    original = np.array(im)
    foreground = remove_background(original)
    blurred = blur(foreground, radius=2)
    polarized = polarize(blurred)

    digits = ocr_digits(Image.fromarray(polarized))

    out = Image.new('RGB', (im.width, 5*im.height), (255, 255, 255))
    y_off = 0

    out.paste(Image.fromarray(original), (0, y_off))
    y_off += im.height
    out.paste(Image.fromarray(foreground), (0, y_off))
    y_off += im.height
    out.paste(Image.fromarray(blurred), (0, y_off))
    y_off += im.height
    out.paste(Image.fromarray(polarized), (0, y_off))
    y_off += im.height

    draw = ImageDraw.Draw(out)
    font = ImageFont.truetype('third-party/DejaVuSansMono.ttf', 50)
    draw.text((0, y_off), digits, (0, 0, 0), font=font)

    return out
