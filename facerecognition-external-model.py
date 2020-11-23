from flask import Flask, request, abort
from functools import wraps
import dlib
import os

app = Flask(__name__)

detector_path = "vendor/models/1/mmod_human_face_detector.dat"
predictor_path = "vendor/models/1/shape_predictor_5_face_landmarks.dat"
face_rec_model_path = "vendor/models/1/dlib_face_recognition_resnet_model_v1.dat"

#app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg']
#app.config['UPLOAD_PATH'] = 'images'

def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        with open('api.key', 'r') as apikey:
            key = apikey.read().replace('\n', '')
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == key:
            return view_function(*args, **kwargs)
        else:
            abort(401)

    return decorated_function

@app.route('/detect', methods=['POST'])
@require_appkey
def detect_faces():
    uploaded_file = request.files['file']

    filename = os.path.basename(uploaded_file.filename)
    uploaded_file.save(filename)

    response = {
      "filename": filename
    }

    detector = dlib.cnn_face_detection_model_v1(detector_path)
    sp = dlib.shape_predictor(predictor_path)
    facerec = dlib.face_recognition_model_v1(face_rec_model_path)

    img = dlib.load_rgb_image(filename)
    dets = detector(img)

    response["faces-count"] = len(dets)

    faces = []
    for k, d in enumerate(dets):
        rec = dlib.rectangle(d.rect.left(), d.rect.top(), d.rect.right(), d.rect.bottom())
        shape = sp(img, rec)
        descriptor = facerec.compute_face_descriptor(img, shape)
        faces.append({
          "detection_confidence": d.confidence,
          "left"                : d.rect.left(),
          "top"                 : d.rect.top(),
          "right"               : d.rect.right(),
          "bottom"              : d.rect.bottom(),
          "landmarks"           : shapeToList(shape),
          "descriptor"          : descriptorToList(descriptor)
        })

    response["faces"] = faces

    os.remove(filename)

    return response;

@app.route('/open')
@require_appkey
def open_model():
    return {
      "preferred_mimetype": "image/jpeg",
      "maximum_area"      : 3840*2160
    }

def shapeToList(shape):
    partList = [];
    for i in range(shape.num_parts):
        partList.append({
          'x': shape.part(i).x,
          'y': shape.part(i).y
        })
    return partList

def descriptorToList(descriptor):
    descriptorList = [];
    for i in range(len(descriptor)):
        descriptorList.append(descriptor[i])
    return descriptorList
