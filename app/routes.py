from datetime import datetime
import os

from flask import render_template, Response, jsonify, request
import face_recognition
import cv2

from app import app, switch, disk_free_mb
from app.webcam import camera, image2bytes, save_image
from config import Config
# from app.forms import LoginForm


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'GET':
        global disk_free_mb

        if switch.value:
            disk_free_mb = int(shutil.disk_usage('.').free / 1024 / 1024)
        data = {
            'record_flag': switch.value,
            'disk_free_mb': disk_free_mb,
            'left_sec': switch.left_sec,
        }
        return jsonify(data), 200

    # method == 'POST'
    if request.json['action'] == 'on':
        switch.on()
    else:
        switch.off()
    return jsonify('OK'), 200

@app.route('/faceid', methods=['GET', 'POST'])
def faceid():
    r = request.get_data()
    im = bytes2image(image)
    face_locations = face_recognition.face_locations(im)
    face_encodings = face_recognition.face_encodings(im, face_locations)
    for (t, r, b, l), face_encoding in zip(face_locations, face_encodings):
        print("Face Bounding Box: ", t, r, b, l)




@app.route('/video_feed')
def video_feed():
    return Response(gen_frame(), mimetype='multipart/x-mixed-replace;'
    'boundary=frame')


def gen_frame():
    ''' commented out stuff is related to hand tracking'''
    # hand_detected = False
    while True:
        frame = camera.get_frame()
        
        if switch.value:
            fname = str(datetime.now().strftime('%m%d_%H:%M:%S:%f')) + '.jpg'  # '0912_03:47:14:263373.jpg'
            save_image(frame, os.path.join(Config.record_path, fname))
        # result, pose = handler.process_image(frame)
        # result.draw_poses(0.15,
        #                   0., handler.crop_full_scale, handler.test_img_copy)
        # if handler.mean_response > FLAGS.confidence:
        #     prediction, probs =  pose_classifier.predict(pose)
        #     labels = {
        #         0: "no_fingers",
        #         1: "index_finger",
        #         2: "two_fingers",
        #         3: "three_fingers",
        #         4: "four_fingers",
        #         5: "five_fingers",
        #         6: "thumbs_up",
        #         7: "thumbs_down"
        #     }
             
        #     result.add_prediction(labels[prediction], probs)
        # pose_frame = image2bytes(result.image_with_poses, mode='RGB')
        pose_frame = image2bytes(frame, mode='RGB')
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + pose_frame + b'\r\n')
