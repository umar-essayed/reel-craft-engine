"""
After Effects Camera & Motion Pipeline for Reel Craft Engine
Provides 2.5D/3D camera transformations, Bézier easing curves, optical motion blur,
RGB chromatic split, anamorphic lens flares, dynamic camera shake, and keyframe interpolation.
All operations are optimized via NumPy and OpenCV Affine / Perspective transforms.
"""

import math
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, Tuple, Optional, List

class BezierEasing:
    """Cubic Bézier easing curves matching After Effects / CSS transition curves."""
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1.0 - math.pow(1.0 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3) / 2.0

    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1.0 if t == 1.0 else 1.0 - math.pow(2.0, -10.0 * t)

    @staticmethod
    def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
        c1 = overshoot
        c3 = c1 + 1.0
        return 1.0 + c3 * math.pow(t - 1.0, 3) + c1 * math.pow(t - 1.0, 2)

    @staticmethod
    def spring_overshoot(t: float, decay: float = 6.0, freq: float = 14.0) -> float:
        """After Effects bounce / overshoot expression."""
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        return 1.0 - math.exp(-t * decay) * math.cos(t * freq)

class CameraState:
    """Represents a camera viewport state in 2.5D space."""
    def __init__(self, x: float = 0.0, y: float = 0.0, zoom: float = 1.0, rotation: float = 0.0,
                 pitch: float = 0.0, yaw: float = 0.0, motion_blur: float = 0.0, chromatic_aberration: float = 0.0):
        self.x = x                          # Pan X offset (px)
        self.y = y                          # Pan Y offset (px)
        self.zoom = zoom                    # Camera focal zoom (1.0 = 100%)
        self.rotation = rotation            # Roll angle (degrees)
        self.pitch = pitch                  # 3D Tilt X (degrees)
        self.yaw = yaw                      # 3D Pan Y (degrees)
        self.motion_blur = motion_blur      # Shutter angle motion blur intensity
        self.chromatic_aberration = chromatic_aberration # Lens edge RGB color fringe

class AECameraEngine:
    """
    Virtual After Effects Camera System.
    Evaluates keyframes, motion paths, lens artifacts, and renders transformed layers.
    """

    @staticmethod
    def evaluate_camera(scene_meta: Dict[str, Any], t_in_scene: float, scene_duration: float) -> CameraState:
        """
        Calculates the camera state at time t within a scene based on camera motions:
        - push_in: Smooth cinematic zoom-in
        - pull_out: Revealing zoom-out
        - whip_pan_left / whip_pan_right: Fast directional whip with motion blur
        - dutch_tilt: Dramatic diagonal roll
        - punch_in: Shock impact cut zoom
        - handheld: Subtle organic camera breathing
        - 3d_orbit: 2.5D perspective yaw & pitch rotation
        """
        dur = max(0.001, scene_duration)
        progress = max(0.0, min(1.0, t_in_scene / dur))

        cam_config = scene_meta.get("camera", {}) if isinstance(scene_meta.get("camera"), dict) else {}
        cam_type = cam_config.get("type", "push_in")
        intensity = float(cam_config.get("intensity", 1.0))

        state = CameraState()

        # 1. Base Motion Profiles
        if cam_type == "push_in":
            # Smooth cinematic zoom-in (from 1.0 to 1.06)
            eased = BezierEasing.ease_out_cubic(progress)
            state.zoom = 1.0 + (0.05 * intensity) * eased
            state.y = - (15.0 * intensity) * eased

        elif cam_type == "pull_out":
            eased = BezierEasing.ease_out_cubic(progress)
            state.zoom = (1.0 + 0.06 * intensity) - (0.06 * intensity) * eased
            state.y = - (10.0 * intensity) * (1.0 - eased)

        elif cam_type == "punch_in":
            # Fast punch in first 200ms, then subtle drift
            punch_dur = 0.22
            if t_in_scene < punch_dur:
                p = t_in_scene / punch_dur
                spring = BezierEasing.spring_overshoot(p, decay=7.0, freq=18.0)
                state.zoom = 1.0 + (0.09 * intensity) * spring
                state.motion_blur = max(0.0, (1.0 - p) * 1.5 * intensity)
                state.chromatic_aberration = max(0.0, (1.0 - p) * 12.0 * intensity)
            else:
                drift_p = (t_in_scene - punch_dur) / max(0.001, (dur - punch_dur))
                state.zoom = 1.0 + (0.09 * intensity) + (0.02 * drift_p)

        elif cam_type == "whip_pan_left":
            # Whip pan in the first 0.3s
            whip_dur = 0.30
            if t_in_scene < whip_dur:
                p = t_in_scene / whip_dur
                eased = BezierEasing.ease_out_expo(p)
                state.x = - (250.0 * intensity) * (1.0 - eased)
                state.motion_blur = (1.0 - p) * 2.5 * intensity
                state.rotation = - (4.0 * intensity) * (1.0 - eased)
            else:
                state.zoom = 1.0 + 0.02 * progress

        elif cam_type == "whip_pan_right":
            whip_dur = 0.30
            if t_in_scene < whip_dur:
                p = t_in_scene / whip_dur
                eased = BezierEasing.ease_out_expo(p)
                state.x = (250.0 * intensity) * (1.0 - eased)
                state.motion_blur = (1.0 - p) * 2.5 * intensity
                state.rotation = (4.0 * intensity) * (1.0 - eased)
            else:
                state.zoom = 1.0 + 0.02 * progress

        elif cam_type == "dutch_tilt":
            eased = BezierEasing.ease_out_cubic(progress)
            state.rotation = - (2.5 * intensity) * eased
            state.zoom = 1.0 + 0.04 * eased

        elif cam_type == "3d_orbit":
            # 2.5D perspective swing
            swing = math.sin(progress * math.pi)
            state.yaw = (12.0 * intensity) * swing
            state.pitch = - (5.0 * intensity) * swing
            state.zoom = 1.0 + (0.04 * intensity) * swing

        elif cam_type == "static":
            state.zoom = 1.0

        # 2. Add Handheld Organic Breathing (unless static)
        if cam_type != "static" and cam_config.get("handheld", True):
            # Dual-frequency Perlin-like organic sway
            sway_x = math.sin(t_in_scene * 1.8) * 3.5 + math.sin(t_in_scene * 3.7) * 1.5
            sway_y = math.cos(t_in_scene * 1.4) * 3.0 + math.cos(t_in_scene * 4.1) * 1.2
            sway_rot = math.sin(t_in_scene * 1.2) * 0.4
            state.x += sway_x * intensity
            state.y += sway_y * intensity
            state.rotation += sway_rot * intensity

        # 3. Dynamic Screen Shake trigger
        shake = cam_config.get("shake")
        if shake and isinstance(shake, dict):
            s_start = float(shake.get("start", 0.0))
            s_dur = float(shake.get("duration", 0.35))
            if s_start <= t_in_scene <= (s_start + s_dur):
                dt = t_in_scene - s_start
                decay = 1.0 - (dt / s_dur)
                s_mag = float(shake.get("intensity", 16.0)) * intensity * decay
                state.x += math.sin(dt * 52.0) * s_mag
                state.y += math.cos(dt * 43.0) * (s_mag * 0.75)
                state.rotation += math.sin(dt * 38.0) * (s_mag * 0.08)
                state.motion_blur = max(state.motion_blur, (s_mag / 16.0) * 1.2)

        return state

    @staticmethod
    def render_motion_blur(cv_img: np.ndarray, blur_amount: float, angle_deg: float = 0.0) -> np.ndarray:
        """Simulates directional camera shutter motion blur (180-degree shutter)."""
        if blur_amount <= 0.05:
            return cv_img

        ksize = int(blur_amount * 12.0)
        if ksize % 2 == 0:
            ksize += 1
        ksize = max(3, min(31, ksize))

        # Generate directional line kernel
        kernel = np.zeros((ksize, ksize), dtype=np.float32)
        rad = math.radians(angle_deg)
        cx, cy = (ksize - 1) / 2.0, (ksize - 1) / 2.0
        length = ksize / 2.0

        x1 = int(round(cx - length * math.cos(rad)))
        y1 = int(round(cy - length * math.sin(rad)))
        x2 = int(round(cx + length * math.cos(rad)))
        y2 = int(round(cy + length * math.sin(rad)))

        cv2.line(kernel, (x1, y1), (x2, y2), 1.0, thickness=1)
        k_sum = kernel.sum()
        if k_sum > 0:
            kernel /= k_sum
        else:
            kernel[int(cy), int(cx)] = 1.0

        return cv2.filter2D(cv_img, -1, kernel)

    @staticmethod
    def apply_chromatic_aberration(cv_img: np.ndarray, shift_px: float) -> np.ndarray:
        """Applies radial or horizontal lens chromatic color splitting."""
        shift = int(round(shift_px))
        if abs(shift) < 1:
            return cv_img

        b, g, r, a = cv2.split(cv_img)
        # Shift red right, blue left
        r_shifted = np.roll(r, shift, axis=1)
        b_shifted = np.roll(b, -shift, axis=1)

        if shift > 0:
            r_shifted[:, :shift] = 0
            b_shifted[:, -shift:] = 0
        else:
            r_shifted[:, shift:] = 0
            b_shifted[:, :-shift] = 0

        return cv2.merge([b_shifted, g, r_shifted, a])

    @classmethod
    def apply_camera_to_canvas(cls, layer: Image.Image, state: CameraState) -> Image.Image:
        """
        Transforms a PIL RGBA layer according to the CameraState using high-speed OpenCV Affine/Perspective.
        Supports 2.5D tilt/yaw, smooth scaling, rotational roll, directional motion blur, and color fringing.
        """
        w, h = layer.size
        # Fast path if no transformation
        if (state.zoom == 1.0 and state.x == 0.0 and state.y == 0.0 and
            state.rotation == 0.0 and state.pitch == 0.0 and state.yaw == 0.0 and
            state.motion_blur == 0.0 and state.chromatic_aberration == 0.0):
            return layer

        # Convert PIL RGBA to NumPy / OpenCV BGRA
        img_np = np.array(layer)
        cv_img = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGRA)

        center_x, center_y = w / 2.0, h / 2.0

        # Check if 3D perspective (pitch or yaw) is active
        has_3d = (abs(state.pitch) > 0.01 or abs(state.yaw) > 0.01)

        if has_3d:
            # 3D Perspective Transformation matrix
            focal_length = 1500.0
            rad_pitch = math.radians(state.pitch)
            rad_yaw = math.radians(state.yaw)
            rad_roll = math.radians(state.rotation)

            # Rotation matrices
            rx = np.array([
                [1, 0, 0, 0],
                [0, math.cos(rad_pitch), -math.sin(rad_pitch), 0],
                [0, math.sin(rad_pitch), math.cos(rad_pitch), 0],
                [0, 0, 0, 1]
            ])
            ry = np.array([
                [math.cos(rad_yaw), 0, math.sin(rad_yaw), 0],
                [0, 1, 0, 0],
                [-math.sin(rad_yaw), 0, math.cos(rad_yaw), 0],
                [0, 0, 0, 1]
            ])
            rz = np.array([
                [math.cos(rad_roll), -math.sin(rad_roll), 0, 0],
                [math.sin(rad_roll), math.cos(rad_roll), 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            r = rz @ ry @ rx

            # Projection & Translation
            src_pts = np.float32([
                [0, 0],
                [w, 0],
                [w, h],
                [0, h]
            ])

            # Perspective transform mapping
            scale = state.zoom
            pts_3d = np.float32([
                [-w / 2, -h / 2, 0, 1],
                [w / 2, -h / 2, 0, 1],
                [w / 2, h / 2, 0, 1],
                [-w / 2, h / 2, 0, 1]
            ])

            transformed_pts = []
            for pt in pts_3d:
                res = r @ pt
                z = res[2] + focal_length
                pz = focal_length / z if z != 0 else 1.0
                px = (res[0] * pz * scale) + center_x + state.x
                py = (res[1] * pz * scale) + center_y + state.y
                transformed_pts.append([px, py])

            dst_pts = np.float32(transformed_pts)
            m = cv2.getPerspectiveTransform(src_pts, dst_pts)
            cv_res = cv2.warpPerspective(cv_img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        else:
            # 2.5D Affine Transformation (Scale + Rotation + Translation)
            m = cv2.getRotationMatrix2D((center_x, center_y), state.rotation, state.zoom)
            m[0, 2] += state.x
            m[1, 2] += state.y
            cv_res = cv2.warpAffine(cv_img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

        # Apply Optical Motion Blur if moving fast
        if state.motion_blur > 0.05:
            cv_res = cls.render_motion_blur(cv_res, state.motion_blur, angle_deg=state.rotation)

        # Apply Chromatic Aberration
        if state.chromatic_aberration > 0.5:
            cv_res = cls.apply_chromatic_aberration(cv_res, state.chromatic_aberration)

        # Convert back to PIL Image
        out_np = cv2.cvtColor(cv_res, cv2.COLOR_BGRA2RGBA)
        return Image.fromarray(out_np)
