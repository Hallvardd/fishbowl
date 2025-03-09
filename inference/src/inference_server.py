from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from io import BytesIO
import numpy as np
import onnxruntime as ort
from PIL import Image
import cv2
import uvicorn

app = FastAPI()

# Load ONNX model
session = ort.InferenceSession("../model/model.onnx")

# data classes
class Fishbowl():
    def __init__(self, bbox: list, mask: np.ndarray):
        self.bbox = bbox
        self.mask = mask
        self.color = (150, 255, 200)
        self.water = None
        self.water_level = 0.0

class Water():
    def __init__(self, bbox: list, mask: np.ndarray):
        self.bbox = bbox
        self.mask = mask
        self.color = (50, 100, 255)


def overlay_mask(image_np: np.ndarray, mask: np.ndarray, color: list, threshold=0.5, alpha=0.3):
    # Resize masks to original image size
    mask = cv2.resize(mask, (image_np.shape[1], image_np.shape[0]), interpolation=cv2.INTER_NEAREST)

    # Apply color map to the mask
    color_mask = image_np.copy()
    color_mask[mask > threshold] = color

    # Overlay mask on original image
    overlay = cv2.addWeighted(image_np, 1 - alpha, color_mask, alpha, 0)

    # Convert to PIL and show
    return overlay


def center_pad_square(image: np.ndarray):
    maxdim = max(image.shape)
    padding = np.zeros((maxdim, maxdim, 3), dtype=np.uint8)
    ypad = int((maxdim - image.shape[0])/2)
    xpad = int((maxdim - image.shape[1])/2)
    padding[ypad: ypad + image.shape[0], xpad: xpad + image.shape[1]] = image
    return padding


def image_to_numpy(image: Image.Image) -> np.ndarray:
    np_image = np.array(image)
    np_image = center_pad_square(np_image)
    np_image = cv2.resize(np_image, (512, 512))
    return np_image

def np_image_to_tensor(np_image: np.ndarray) -> np.ndarray:
    tensor = np_image/255.0
    tensor = tensor.astype(np.float32)
    tensor = np.expand_dims(tensor, axis=0)
    tensor = tensor.transpose(0, 3, 1, 2)
    return tensor


def postprocess_results(image: np.ndarray, outputs: tuple) -> dict:
    """Overlay results on image and generate metadata"""
    # Extract outputs
    fishbowls = calculate_water_level(outputs)
    image_np = image.copy()

    # Overlay masks and bounding boxes for the water and bowl
    for fbowl in fishbowls:
        image_np = draw_mask_and_bbox(fbowl, image_np)
        if fbowl.water is not None:
            image_np = draw_mask_and_bbox(fbowl.water, image_np)

    # return as array since PIL is being weird about it
    return {"image": image_np, "fishbowls": fishbowls}

def draw_mask_and_bbox(obj: object, image_np: np.ndarray) -> np.ndarray:
    (x1, y1, x2, y2) = obj.bbox
    image_np = overlay_mask(image_np, obj.mask, obj.color)
    #cv2.rectangle(image_np, (x1, y1), (x2, y2), obj.color, 1)
    return image_np


def calculate_water_level(outputs: tuple) -> list[Fishbowl]:
    """
    Calculate water level from image
    First sort by category, and find over lapping pairs
    """
    bboxes, labels, scores, masks = outputs

    bowls = [(bbox, np.squeeze(mask, axis=0)) for bbox, label, score, mask in zip(bboxes, labels, scores, masks) if label == 1]
    waters = [(bbox, np.squeeze(mask, axis=0)) for bbox, label, score, mask in zip(bboxes, labels, scores, masks) if label == 2]

    fishbowls = []
    # find the overlapping bowl and water bbox, bbox format xyxy
    for bowl_bbox, bowl_mask in bowls:
        biggest_overlap = 0
        bowl_bbox = bowl_bbox.astype(int)
        fishbowl = Fishbowl(bowl_bbox, bowl_mask)
        # find the water level bbox that has the biggest overlap with the bowl
        for water_bbox, water_mask in waters:
            water_bbox = water_bbox.astype(int)
            x1 = max(bowl_bbox[0], water_bbox[0])
            y1 = max(bowl_bbox[1], water_bbox[1])
            x2 = min(bowl_bbox[2], water_bbox[2])
            y2 = min(bowl_bbox[3], water_bbox[3])
            inter_area = max(0, x2 - x1 + 1) * max(0, y2 - y1 + 1)
            # also check if the overlapping area is atleast 50% of the water level bbox
            water_area = abs(water_bbox[2] - water_bbox[0]) * abs(water_bbox[3] - water_bbox[1])
            if inter_area > biggest_overlap and inter_area > water_area * 0.5:
                biggest_overlap = inter_area
                fishbowl.water = Water(water_bbox, water_mask)
        fishbowls.append(fishbowl)

    for fishbowl in fishbowls:
        if fishbowl.water is not None:
            print("Calculating water volume")
            water_volume = calculate_volume(fishbowl.water)
            print("Calculating bowl volume")
            bowl_volume = calculate_volume(fishbowl)
            print(f"Water volume: {water_volume}, Bowl volume: {bowl_volume}")
            print(f"Calculated water volume: {water_volume / bowl_volume}")
            fishbowl.water_level = np.count_nonzero(fishbowl.water.mask > 0.5) / np.count_nonzero(fishbowl.mask > 0.5)
    return fishbowls



def calc_volume_argmax(obj: object, step=1) -> float:
    bbox = obj.bbox
    print("bbox: ", bbox)
    xmin = bbox[0]
    xmax = bbox[2]
    ymin = bbox[1]
    ymax = bbox[3]
    center = int((xmin + xmax) / 2)
    volume = 0.0

    for y in range(ymin, ymax, step):
        segments = []
        start = None
        # process the left hand side of the center line
        volume += np.where([y,...] > 0.5, 1, 0).max(axis=1)
        print(f"index: {y}, segments: {segments} ")
    return volume


def calculate_volume(obj: object, step=1) -> float:
    bbox = obj.bbox
    x1 = max(bbox[0], 0)
    x2 = min(bbox[2], obj.mask.shape[1]-1)
    y1 = max(bbox[1], 0)
    y2 = min(bbox[3], obj.mask.shape[0]-1)
    center = int((x1 + x2) / 2)
    volume = 0.0
    # helper function
    def get_segments(y, start_idx, end_idx) -> list:
        segments = []
        start = None
        # procress from the egde of the object to the center
        for x in range(start_idx, end_idx, 1 if start_idx - end_idx < 0 else -1):
            if obj.mask[y, x] > 0.5 and start is None:
                start = x
            elif obj.mask[y, x] < 0.5 and start is not None:
                segments.append((abs(center - start), abs(center - x)))
                start = None
        # if the object ends at the end at the center
        if start is not None:
            segments.append((abs(center - start), 0))
        return segments

    for y in range(y1, y2, step):
        segments = []
        start = None
        # process the left hand side of the center line
        segments += get_segments(y, x1, center)
        segments += get_segments(y, x2, center)
        for seg in segments:
                volume += np.pi*0.5*(seg[0]**2 - seg[1]**2)
    return volume


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """Receives image, runs ONNX model, and returns processed image + metadata"""
    image = Image.open(BytesIO(await file.read())).convert("RGB")
    image = image_to_numpy(image)
    input_tensor = numpy_to_tensor(image)
    outputs = session.run(None, {"input": input_tensor})
    processed_data = postprocess_results(image, outputs)

    # Unpack the dictionary
    processed_image = processed_data["image"]
    metadata = [fb.water_level for fb in processed_data["fishbowls"]]

    # convert to PIL image
    processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
    processed_image = Image.fromarray(processed_image)

    # Convert image to bytes
    img_byte_arr = BytesIO()
    processed_image.save(img_byte_arr, format="JPEG")
    img_byte_arr = img_byte_arr.getvalue()

    return JSONResponse(content={
        "image": img_byte_arr.hex(),
        "metadata": metadata
    })

def dummy_run():
    image = Image.open("../test.jpg")
    image = image_to_numpy(image)
    input_tensor = np_image_to_tensor(image)
    outputs = session.run(None, {"input": input_tensor})
    processed_data = postprocess_results(image, outputs)

    # unpack the dictionary
    processed_image = processed_data["image"]
    metadata = processed_data["fishbowls"]

    for fbowl in metadata:
        print(f"Bowl: {fbowl.bbox}, Water level: {fbowl.water_level}")

    # show the image
    print(f"Processed image shape: {processed_image.shape}")
    cv2.imshow("image", cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB))
    cv2.waitKey(0)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
