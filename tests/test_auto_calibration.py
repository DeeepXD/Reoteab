import pytest

import biome_tracker.mixin_calib as calibration
from biome_tracker.mixin_calib import LandmarkMatch, _find_indicator_candidates, select_stable_indicator


def test_indicator_candidates_use_the_center_between_template_halves():
    candidates = _find_indicator_candidates(
        [LandmarkMatch(40, 60, 0.91)],
        [LandmarkMatch(47, 61, 0.93)],
        template_width=7,
        template_height=15,
    )

    assert len(candidates) == 1
    assert (candidates[0].x, candidates[0].y) == (47, 68)


@pytest.mark.skipif(calibration.np is None, reason="OpenCV dependencies are unavailable")
def test_templates_find_a_fish_indicator_pair_in_a_frame():
    left_template = calibration._decode_template(calibration.FISH_DETECT_LEFT_TEMPLATE)
    right_template = calibration._decode_template(calibration.FISH_DETECT_RIGHT_TEMPLATE)
    frame = calibration.np.zeros((80, 100, 3), dtype=calibration.np.uint8)
    frame[30:45, 40:47] = left_template
    frame[30:45, 47:54] = right_template

    candidates = _find_indicator_candidates(
        calibration._find_template_matches(frame, left_template),
        calibration._find_template_matches(frame, right_template),
        template_width=7,
        template_height=15,
    )

    assert any(candidate.x == 47 and candidate.y == 38 for candidate in candidates)


def test_stable_indicator_uses_matching_candidates_from_each_frame():
    match = select_stable_indicator([
        [LandmarkMatch(100, 200, 0.92)],
        [LandmarkMatch(101, 200, 0.90)],
        [LandmarkMatch(100, 201, 0.94)],
    ])

    assert match is not None
    assert (match.x, match.y) == (100, 200)
    assert match.confidence > 0.9


def test_stable_indicator_rejects_unstable_candidates():
    match = select_stable_indicator([
        [LandmarkMatch(100, 200, 0.95)],
        [LandmarkMatch(120, 200, 0.95)],
        [LandmarkMatch(100, 200, 0.95)],
    ])

    assert match is None
