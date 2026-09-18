import base64
from dataclasses import dataclass
from typing import Any

try:
    import cv2
    import mss
    import numpy as np
except Exception:
    cv2 = None
    mss = None
    np = None


FISH_INDICATOR_SEARCH_REGION = (0.5, 0.6, 0.3, 0.4)
FISH_INDICATOR_MIN_CONFIDENCE = 0.8
FISH_INDICATOR_FRAME_COUNT = 3

FISH_DETECT_LEFT_TEMPLATE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAcAAAAPCAYAAAAoAdW+AAAAAXNSR0IArs4c6QAAAARn"
    "QU1BAACxjwv8YQUAAAAJcEhZcwAADsIAAA7CARUoSoAAAAGHaVRYdFhNTDpjb20uYWRv"
    "YmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49J++7vycgaWQ9J1c1TTBNcENlaGlIenJl"
    "U3pOVGN6a2M5ZCc/Pg0KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyI+"
    "PHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJk"
    "Zi1zeW50YXgtbnMjIj48cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0idXVpZDpmYWY1"
    "YmRkNS1iYTNkLTExZGEtYWQzMS1kMzNkNzUxODJmMWIiIHhtbG5zOnRpZmY9Imh0dHA6"
    "Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIj48dGlmZjpPcmllbnRhdGlvbj4xPC90aWZm"
    "Ok9yaWVudGF0aW9uPjwvcmRmOkRlc2NyaXB0aW9uPjwvcmRmOlJERj48L3g6eG1wbWV0"
    "YT4NCjw/eHBhY2tldCBlbmQ9J3cnPz4slJgLAAAA4UlEQVQoU22QP0tCcRiFj235cYKg"
    "oaGhT1A02dbQoqZ1496Mq4iDLjo4C0UohotT0NCQVzAcL9efVwkDP8nTEPgnfwfe6YHn"
    "cN4EAllSrDYkBP/voVLHzL7ZgY5fI54veO72SWxqy7WmTk+OtfhZ6v1jsNbmvQrBaEyv/"
    "8Z56hrEnzbnFjHxnKf2K2epq1WFbgtlwsjQeulwcbkGCPaODg+UTO5r9DVWr93a3pNzH"
    "wmjyc6cVWf2zsFMZ3aI4MbxGAwDO0Tgl3yC4acdIsg7GaaxsUME926aaBJuv28zXiGr"
    "X1Z/+c+SaPxXAAAAAElFTkSuQmCC"
)

FISH_DETECT_RIGHT_TEMPLATE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAcAAAAPCAYAAAAoAdW+AAAAAXNSR0IArs4c6QAAAARn"
    "QU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAGHaVRYdFhNTDpjb20uYWRv"
    "YmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49J++7vycgaWQ9J1c1TTBNcENlaGlIenJl"
    "U3pOVGN6a2M5ZCc/Pg0KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyI+"
    "PHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJk"
    "Zi1zeW50YXgtbnMjIj48cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0idXVpZDpmYWY1"
    "YmRkNS1iYTNkLTExZGEtYWQzMS1kMzNkNzUxODJmMWIiIHhtbG5zOnRpZmY9Imh0dHA6"
    "Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIj48dGlmZjpPcmllbnRhdGlvbj4xPC90aWZm"
    "Ok9yaWVudGF0aW9uPjwvcmRmOkRlc2NyaXB0aW9uPjwvcmRmOlJERj48L3g6eG1wbWV0"
    "YT4NCjw/eHBhY2tldCBlbmQ9J3cnPz4slJgLAAAA80lEQVQoU22OMUtCcRTFTwXxItz6"
    "DkZBFASOLUHQ1hA0JTQFJRVPLYlCbRCqpa0xhSgCzXJNkJ4tgkO853th+Fl+DfKyx78D"
    "By73xz33KFe8BvGv5fp90mclAyBQ5eEZ/+sb+7RgwInJ2Ew+Nm0psbykcrymlbeEfoVg"
    "YytJ9aXBR6fLeelqFBsOm9s7PNUb9AcD8pfDkmMIwpTk7oHW11a1MDerx+qrxkcPpPLt"
    "jd5bTU1Zlhbn44pchvJcT5X7u2Ghv/aDHnb2KFoIgdN2sDP7Zlun7VC4KEZShCAIeqSz"
    "hxGAQK73SeYkZQAEOs7tGcvQP7E8+gdCud3IAAAAAElFTkSuQmCC"
)


@dataclass(frozen=True)
class LandmarkMatch:
    x: int
    y: int
    confidence: float


def _decode_template(encoded: str):
    if cv2 is None or np is None:
        return None
    return cv2.imdecode(np.frombuffer(base64.b64decode(encoded), dtype=np.uint8), cv2.IMREAD_COLOR)


def _template_mask(template):
    mask = np.ones(template.shape[:2], dtype=np.uint8)
    mask[np.all(template == [255, 0, 255], axis=-1)] = 0
    return mask


def _find_template_matches(frame, template, top_n=4):
    if cv2 is None or np is None or template is None:
        return []

    result = cv2.matchTemplate(frame, template, cv2.TM_CCORR_NORMED, mask=_template_mask(template))
    result[np.isinf(result) | np.isnan(result)] = 0
    peaks = result == cv2.dilate(result, np.ones((3, 3), dtype=np.uint8))
    y_values, x_values = np.where(peaks & (result >= FISH_INDICATOR_MIN_CONFIDENCE))
    scores = result[y_values, x_values]
    order = np.argsort(scores)[::-1][:top_n]
    return [
        LandmarkMatch(int(x_values[index]), int(y_values[index]), float(scores[index]))
        for index in order
    ]


def _find_indicator_candidates(left_matches, right_matches, template_width, template_height):
    candidates = []
    for left in left_matches:
        for right in right_matches:
            spacing = right.x - left.x
            if abs(left.y - right.y) > 3 or spacing < template_width - 2 or spacing > template_width + 4:
                continue
            candidates.append(LandmarkMatch(
                round((left.x + right.x + template_width) / 2),
                round((left.y + right.y + template_height) / 2),
                (left.confidence + right.confidence) / 2,
            ))
    return candidates


def select_stable_indicator(candidates_by_frame):
    if len(candidates_by_frame) < FISH_INDICATOR_FRAME_COUNT:
        return None

    best = None
    for first in candidates_by_frame[0]:
        matches = [first]
        for candidates in candidates_by_frame[1:]:
            nearby = [
                candidate for candidate in candidates
                if abs(candidate.x - first.x) <= 3 and abs(candidate.y - first.y) <= 3
            ]
            if not nearby:
                break
            matches.append(max(nearby, key=lambda candidate: candidate.confidence))
        if len(matches) != len(candidates_by_frame):
            continue
        confidence = sum(candidate.confidence for candidate in matches) / len(matches)
        candidate = LandmarkMatch(
            round(sum(item.x for item in matches) / len(matches)),
            round(sum(item.y for item in matches) / len(matches)),
            confidence,
        )
        if best is None or candidate.confidence > best.confidence:
            best = candidate
    return best


def _roblox_bounds(tracker):
    if tracker is None or not hasattr(tracker, "_find_roblox_hwnds"):
        return None
    try:
        hwnds = tracker._find_roblox_hwnds()
        if not hwnds:
            return None
        import win32gui
        left, top, right, bottom = win32gui.GetWindowRect(hwnds[0])
        if right <= left or bottom <= top:
            return None
        return left, top, right - left, bottom - top
    except Exception:
        return None


def auto_calibrate_fishing_detect_pixel(tracker=None):
    if cv2 is None or mss is None or np is None:
        return {"success": False, "error": "Auto calibration dependencies are unavailable."}

    bounds = _roblox_bounds(tracker)
    if bounds is None:
        return {"success": False, "error": "Roblox is not open."}

    left, top, width, height = bounds
    x_ratio, y_ratio, width_ratio, height_ratio = FISH_INDICATOR_SEARCH_REGION
    region = {
        "left": left + round(width * x_ratio),
        "top": top + round(height * y_ratio),
        "width": round(width * width_ratio),
        "height": round(height * height_ratio),
    }
    left_template = _decode_template(FISH_DETECT_LEFT_TEMPLATE)
    right_template = _decode_template(FISH_DETECT_RIGHT_TEMPLATE)
    if left_template is None or right_template is None:
        return {"success": False, "error": "Fishing indicator templates could not be loaded."}

    candidates_by_frame = []
    try:
        with mss.mss() as screen:
            for _ in range(FISH_INDICATOR_FRAME_COUNT):
                frame = np.array(screen.grab(region))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                left_matches = _find_template_matches(frame, left_template)
                right_matches = _find_template_matches(frame, right_template)
                candidates_by_frame.append(
                    _find_indicator_candidates(
                        left_matches,
                        right_matches,
                        left_template.shape[1],
                        left_template.shape[0],
                    )
                )
    except Exception as error:
        return {"success": False, "error": f"Could not capture the Roblox window: {error}"}

    match = select_stable_indicator(candidates_by_frame)
    if match is None:
        return {
            "success": False,
            "error": "Fish indicator was not found. Start fishing and keep the indicator visible, then try again.",
        }

    return {
        "success": True,
        "key": "fishing_detect_pixel",
        "value": [region["left"] + match.x, region["top"] + match.y],
        "confidence": round(match.confidence, 3),
    }
