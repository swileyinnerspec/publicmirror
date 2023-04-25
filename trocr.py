from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import numpy as np
from PIL import Image
import requests
import sys
import cv2

blocksize = 51

mname='microsoft/trocr-large-handwritten'
processor = TrOCRProcessor.from_pretrained(mname)
model = VisionEncoderDecoderModel.from_pretrained(mname)
def linetotext(img):
    # Show the image in a window
#    cv2.imshow('Line of Text', image)
#    cv2.waitKey(0)
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pixel_values = processor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(generated_text)


def rotimg(img,angle):
    img_center = tuple(np.array(img.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(img_center, angle, 1.0)
    rotated = cv2.warpAffine(img, rot_mat, img.shape[1::-1], flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated
def deskew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, blocksize, 10)
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    angles = []
    for cnt in contours:
        rect = cv2.minAreaRect(cnt)
        angle = rect[2]-45
        #if angle < -45:
        #    angle += 90
        angles.append(angle)
    median_angle = np.median(angles)
    return rotimg(img,median_angle)
def find_lines(image_path):
    # Load the image
    image = deskew(cv2.imread(image_path))

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, blocksize, 20)
    blend = cv2.addWeighted(gray, 0.8, bw, 0.2, 0)
    # Apply a Gaussian blur to the image
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply adaptive thresholding to the image
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, blocksize, 10)

    # Find contours in the image
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort the contours from top to bottom
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

    # Keep track of the last y-coordinate of a contour
    last_y = -1

    # Iterate over the contours and call linetotext for each one
    for contour in contours:
        # Get the bounding box for the contour
        x, y, w, h = cv2.boundingRect(contour)

        if h < 8:
            continue
        if y> h/4:
            y = y- int(h/4)
        h=h+int(h/2)
        # Reject overlapping contours
        if last_y >= 0 and y < last_y + h // 2:
            continue
        # Stretch the contour to be the full width of the image
        x = 0
        w = image.shape[1]

        # Extract the line of text from the image
        line_image = blend[y:y+h, x:x+w]
        rotimg(line_image,cv2.minAreaRect(contour)[2])

        # Call linetotext on the line of text
        linetotext(line_image)

        # Update last_y
        last_y = y

if __name__ == '__main__':
    # Get the image path from the command line arguments
    if len(sys.argv) < 2:
        print('Usage: python linetotext.py <image_path>')
        sys.exit(1)
    image_path = sys.argv[1]

    find_lines(image_path)

    # Destroy all windows
    cv2.destroyAllWindows()
