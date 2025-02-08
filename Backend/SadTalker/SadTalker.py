import os
import shutil
import torch
import time
from src.utils.preprocess import CropAndExtract
from src.test_audio2coeff import Audio2Coeff  
from src.facerender.animate import AnimateFromCoeff
from src.generate_batch import get_data
from src.generate_facerender_batch import get_facerender_data
from src.utils.init_path import init_path

class SadTalker:
    def __init__(self, checkpoint_dir='./checkpoints', result_dir='./results', device=None):
        self.checkpoint_dir = checkpoint_dir
        self.result_dir = result_dir

        if device:
            self.device = device
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.sadtalker_paths = init_path(
            self.checkpoint_dir, 
            os.path.join(os.path.dirname(__file__), 'src', 'config'),  
            size=256, old_version=False, preprocess='crop'
        )

        self.preprocess_model = CropAndExtract(self.sadtalker_paths, self.device)
        self.audio_to_coeff = Audio2Coeff(self.sadtalker_paths, self.device)
        self.animate_from_coeff = AnimateFromCoeff(self.sadtalker_paths, self.device)

    def generate_video(self, source_image, driven_audio, 
                       pose_style=0, batch_size=2, size=256, 
                       enhancer=None, still_mode=False, 
                       ref_eyeblink=None, ref_pose=None, 
                       input_yaw=None, input_pitch=None, input_roll=None,
                       verbose=False):
        save_dir = os.path.join(self.result_dir, time.strftime("%Y_%m_%d_%H.%M.%S"))
        os.makedirs(save_dir, exist_ok=True)

        first_frame_dir = os.path.join(save_dir, 'first_frame_dir')
        os.makedirs(first_frame_dir, exist_ok=True)

        first_coeff_path, crop_pic_path, crop_info = self.preprocess_model.generate(
            source_image, first_frame_dir, 'crop', source_image_flag=True, pic_size=size
        )

        if first_coeff_path is None:
            raise ValueError("Failed to extract 3DMM coefficients, the input image may have issues.")

        def process_reference_video(ref_video, save_name):
            if ref_video:
                ref_dir = os.path.join(save_dir, save_name)
                os.makedirs(ref_dir, exist_ok=True)
                return self.preprocess_model.generate(ref_video, ref_dir, 'crop', source_image_flag=False)[0]
            return None
        
        ref_eyeblink_coeff_path = process_reference_video(ref_eyeblink, "ref_eyeblink")
        ref_pose_coeff_path = ref_eyeblink_coeff_path if ref_pose == ref_eyeblink else process_reference_video(ref_pose, "ref_pose")

        batch = get_data(first_coeff_path, driven_audio, self.device, ref_eyeblink_coeff_path, still=still_mode)
        coeff_path = self.audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path)

        data = get_facerender_data(coeff_path, crop_pic_path, first_coeff_path, driven_audio, batch_size,
                                   input_yaw_list=input_yaw, input_pitch_list=input_pitch, input_roll_list=input_roll,
                                   expression_scale=1.0, still_mode=still_mode, preprocess='crop', size=size)
        result_video = self.animate_from_coeff.generate(data, save_dir, source_image, crop_info, enhancer=enhancer,
                                                        background_enhancer=None, preprocess='crop', img_size=size)

        final_video_path = save_dir + '.mp4'
        shutil.move(result_video, final_video_path)

        if not verbose:
            try:
                shutil.rmtree(save_dir)
            except Exception as e:
                print(f"Warning: Failed to delete temp directory {save_dir}: {e}")

        return final_video_path