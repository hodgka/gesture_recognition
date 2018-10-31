import time
from threading import Thread
import requests

import cv2
import numpy as np
from config import Config

class BaseCamera:
    frame_height = 0
    frame_width = 0

    def get_frame(self):
        raise NotImplementedError

class Webcam(BaseCamera):
    def __init__(self, device_number=0):
        class CapThread(Thread):
            def __init__(self, thread_cap):
                super().__init__()
                self.cap = thread_cap
                self.frame = None
                self.stop_flag = False

            def stop(self):
                self.stop_flag = True

            def clear_buff(self):
                start_sec = time.time()
                count = 0
                elapsed_sec = 0
                print("Clearing Buffer...")
                while count <= 50:
                    elapsed_sec = time.time() - start_sec
                    if elapsed_sec > 20:
                        raise Exception("Timeout -", elapsed_sec)
                    ret = self.cap.grab()
                    if ret:
                        count += 1
                print("Grabbed first 50 frames in {}"
                "seconds...".format(elapsed_sec))
            
            def run(self, verbose=True):
                self.clear_buff()
                count = 0
                start_sec = time.time()
                while True:
                    if self.stop_flag:
                        break

                    ret, frame = self.cap.read()
                    if not ret:
                        raise Exception(
                               "Failed to read frame. Check webcam...")
                    self.frame = frame
                    if verbose:
                        count += 1
                        if count % 100 == 0:
                            elapsed_sec = time.time() - start_sec
                            print("CapThread FPS: {}".format(100/elapsed_sec))
                            start_sec = time.time()
                            count = 0
        cap = cv2.VideoCapture(device_number)
        print("CAP_PROP_BUFFERSIZE:{}".format(cap.get(cv2.CAP_PROP_BUFFERSIZE)))
        self.cap_thread = CapThread(cap)
        self.cap_thread.start()
        print("Waiting for first frame from camera: {}".format(device_number))
        self._wait_for_first_frame()
        print("Camera is ready...")

    def _wait_for_first_frame(self):
        for _ in range(50):
            if self.cap_thread.frame is not None:
                return
            time.sleep(0.1)
        raise Exception("Could not load first frame for 5 seconds...")
    
    def get_frame(self, mode="RGB"):
        if mode == 'RGB':
            return convert_to_rgb(self.cap_thread.frame)
        elif mode == 'BGR':
            return self.cap_thread.frame
        else:
            raise ValueError("Invalid mode: " + mode)

    def release(self):
        self.cap_thread.stop()
        while self.cap_thread.is_alive():
            time.sleep(0.1)

class VideoCaptureInfo:
    """
    >>> cap = cv2.VideoCapture('test_video/video1.mp4')
    >>> info = VideoCaptureInfo(cap)
    >>> print(info)
    <VideoCaptureInfo>
      fps: 10.0
      frame_count: 100
      frame_height: 720
      frame_width: 960
    """
    def __init__(self, cap):
        self.frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)  # type: float

    def __str__(self):
        str_list = ['<%s>' % self.__class__.__name__]
        for key in sorted(self.__dict__):
            str_list.append("  %s: %s" % (key, getattr(self, key)))
        return '\n'.join(str_list)

class VideoWriter(object):
    """
    Write jpg frames into video

    >>> video_writer = VideoWriter('test_frames/video.mp4', fps=10., frame_width=960, frame_height=720)
    >>> image1 = load_image('test_frames/0000.jpg')
    >>> image2 = load_image('test_frames/0001.jpg')
    >>> image3 = load_image('test_frames/0002.jpg')
    >>> for _ in range(10):
    ...     video_writer.write_frame(image1)
    ...     video_writer.write_frame(image2)
    ...     video_writer.write_frame(image3)
    >>> video_writer.done()
    video has been written to test_frames/video.mp4
    """
    def __init__(self, path_to_out, fps, frame_height, frame_width, mode='RGB'):
        assert_mode(mode)
        self.mode = mode
        self.path_to_out = path_to_out
        self.frame_width = frame_width
        self.frame_height = frame_height

        forcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out_video = cv2.VideoWriter(
            str(path_to_out), forcc, fps, (frame_width, frame_height))

    def write_frame(self, frame):
        if self.mode == 'RGB':
            frame = convert_to_bgr(frame)
        self.out_video.write(frame)

    def done(self):
        """Call this method to finish writing frames"""
        self.out_video.release()
        print('video has been written to %s' % self.path_to_out)

    @classmethod
    def from_video(cls, path_to_video, path_to_out):
        """Return VideoWrite with same fps, width, height as original video"""
        _, cap_info = load_video(path_to_video)
        return cls(path_to_out, fps=cap_info.fps,
                   frame_height=cap_info.frame_height,
                   frame_width=cap_info.frame_width,)


def convert_to_rgb(frame):
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def convert_to_bgr(frame):
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def image2bytes(image, mode='RGB', ext='.jpg', quality=95):
    """
    Convert image to jpeg binary

    >>> image = load_image('test_images/apple1.jpg')
    >>> image_bin = image2bytes(image, quality=100)
    >>> image2 = bytes2image(image_bin)
    >>> save_image(image2, 'temp/apple1_new.jpg')

    # test .png will be loss less
    >>> image_bin = image2bytes(image, ext='.png')
    >>> image3 = bytes2image(image_bin)
    >>> diff = image3 - image
    >>> diff.mean()
    0.0
    """
    if mode == 'RGB':
        image = convert_to_bgr(image)
    encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
    return cv2.imencode(ext, image, encode_param)[1].tobytes()


def bytes2image(bin, mode='RGB'):
    buff = np.frombuffer(bin, dtype=np.uint8)
    img_array = cv2.imdecode(buff, 3)
    if mode == 'RGB':
        return convert_to_rgb(img_array)
    return img_array  # BGR

# def load_video(path_to_video, verbose=False):
#     """
#     >>> _ = load_video('test_video/video1.mp4', verbose=True)
#     <VideoCaptureInfo>
#       fps: 10.0
#       frame_count: 100
#       frame_height: 720
#       frame_width: 960
#     """
#     cap = cv2.VideoCapture(str(path_to_video))
#     cap_info = VideoCaptureInfo(cap)
#     if verbose:
#         print(cap_info, flush=True)
#     return cap, cap_info


# def video_frames_iterator(path_to_video, mode='RGB'):
#     """
#     >>> images = video_frames_iterator('test_video/video10.mp4')
#     >>> image_list = list(images)
#     >>> len(image_list)
#     10
#     >>> isinstance(image_list[-1], np.ndarray)  # make sure last frame is loaded
#     True
#     """
#     assert_mode(mode)
#     cap, cap_info = load_video(path_to_video)
#     for _ in range(cap_info.frame_count):
#         _, frame = cap.read()
#         if mode == 'RGB':
#             frame = convert_to_rgb(frame)
#         yield frame
#     cap.release()


# def video2jpg(path_to_video, output_folder, verbose=False):
#     """
#     jpg starts from 0.jpg (0-indexed)

#     >>> video2jpg('test_video/video1.mp4', 'test_video')
#     """
#     cap, cap_info = load_video(path_to_video, verbose)
#     digits = len(str(cap_info.frame_count))
#     fname_format = r'%0' + str(digits) + 'd.jpg'  # e.g. 0001.jpg

#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     output_folder = Path(output_folder)

#     for idx in tqdm(range(cap_info.frame_count)):
#         _, image = cap.read()
#         fname = output_folder / (fname_format % idx)
#         save_image(image, str(fname))


# def shorten_video(path_to_video, new_frame_count, path_to_out, verbose=False):
#     """
#     >>> shorten_video('test_video/video1.mp4', 10, 'test_video/video10.mp4')
#     """
#     cap, cap_info = load_video(path_to_video, verbose)
#     if new_frame_count > cap_info.frame_count:
#         raise Exception('new_frame_count must <= frame_count=%s'
#                         % cap_info.frame_count)

#     video_writer = VideoWriter(
#         path_to_out, cap_info.fps, cap_info.frame_width, cap_info.frame_height)
#     for _ in tqdm(range(new_frame_count)):
#         _, frame = cap.read()
#         video_writer.write_frame(frame)

#     video_writer.done()



def save_image(img, path, mode='RGB'):
    """Use mode=RGB for rgb input image

    >>> img = load_image(Path('test_images/apple1.jpg'))
    >>> save_image(img, Path('test_images/apple1_copy:123.jpg'))
    """
    assert_mode(mode)
    if mode == 'RGB':
        img = convert_to_bgr(img)

    cv2.imwrite(str(path), img)

def assert_mode(mode):
    valid = {'cv2', 'RGB'}
    if mode not in valid:
        raise Exception('mode must be in %s' % valid)



camera = Webcam(Config.camera)

if __name__ == "__main__":
    camera = Webcam(0)
    while True:
        frame = camera.get_frame()
