#!/usr/bin/env python3
"""G1 主体完整性：人物 → MediaPipe Pose 关键点计数；非人物 → u2net 掩膜连通性。"""
import numpy as np
import mediapipe as mp
from PIL import Image

from .u2net import foreground_mask

# 肢体关键点组（MediaPipe Pose 索引）：肩肘腕 / 髋膝踝
UPPER = [(11, 13, 15), (12, 14, 16)]   # 左右上臂+前臂
LOWER = [(23, 25, 27), (24, 26, 28)]   # 左右大腿+小腿

_pose = None


def _get_pose():
    global _pose
    if _pose is None:
        _pose = mp.solutions.pose.Pose(
            static_image_mode=True, model_complexity=1,
            min_detection_confidence=0.4)
    return _pose


def _limb_visible(landmarks, idxs, vis_min=0.5):
    return all(lm.visibility >= vis_min for lm in [landmarks[i] for i in idxs])


def _pose_limbs(rgb: np.ndarray, vis_min: float):
    """返回 {detected: bool, upper: list[bool], lower: list[bool], n_keypoints}"""
    results = _get_pose().process(rgb)
    if not results.pose_landmarks:
        return {'detected': False, 'upper': [], 'lower': [], 'n_keypoints': 0}
    lm = results.pose_landmarks.landmark
    n_kp = sum(1 for l in lm if l.visibility >= vis_min)
    upper = [_limb_visible(lm, g, vis_min) for g in UPPER]
    lower = [_limb_visible(lm, g, vis_min) for g in LOWER]
    return {'detected': True, 'upper': upper, 'lower': lower, 'n_keypoints': n_kp}


def _mask_connectivity(mask: np.ndarray, major_min: float, frag_max: int):
    from scipy import ndimage
    bw = (mask > 0.5).astype(np.uint8)
    labels, n = ndimage.label(bw)
    if n == 0:
        return {'major_ratio': 0.0, 'fragments': 0, 'ok': False}
    sizes = ndimage.sum(bw, labels, range(1, n + 1))
    major = sizes.max() / max(bw.sum(), 1)
    return {'major_ratio': float(major), 'fragments': int(n),
            'ok': major >= major_min and n <= frag_max}


def run(subject_path, thr):
    """thr: qa_thresholds['default']（含 g1_* 阈值）→ {pass, score, issues, mode, detail}"""
    img = Image.open(subject_path).convert('RGBA')
    rgb = np.asarray(img.convert('RGB'))
    vis_min = thr.get('g1_pose_visibility', 0.6)

    pose = _pose_limbs(rgb, vis_min)
    if pose['detected'] and pose['n_keypoints'] >= 5:
        issues = []
        warnings = []
        if any(not u for u in pose['upper']):
            issues.append('上肢缺失')
        if any(not l_ for l_ in pose['lower']):
            # 半身像/特写卡合法：下肢缺失降为预警
            warnings.append('下肢未检测（半身像？）')
        ok = not issues
        return {
            'pass': ok, 'mode': 'pose', 'score': pose['n_keypoints'] / 33,
            'issues': issues, 'warnings': warnings,
            'detail': {'n_keypoints': pose['n_keypoints'],
                       'upper_ok': pose['upper'], 'lower_ok': pose['lower']},
        }

    # 非人物：掩膜连通性
    mask = foreground_mask(img)
    conn = _mask_connectivity(mask, thr.get('g1_mask_major_ratio', 0.75),
                              thr.get('g1_mask_fragments_max', 4))
    return {
        'pass': conn['ok'], 'mode': 'mask', 'score': conn['major_ratio'],
        'issues': [] if conn['ok'] else ['掩膜断裂/碎片多'],
        'detail': conn,
    }
