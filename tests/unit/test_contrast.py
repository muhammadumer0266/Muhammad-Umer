"""WCAG contrast ratios for the design-token pairs.

Computed independently of the CSS file so this test fails loudly if a token
value drifts below AA (4.5:1 body text, 3:1 large text) without anyone
noticing during a color tweak.
"""

TOKENS = {
    "bg": "#0d0910",
    "ink": "#f7f1e9",
    "soft": "#e0d6cd",
    "mute": "#ab9fa8",
    "accent": "#d9b8a3",
    "accent-hi": "#f2d8c6",
}


def _srgb_to_linear(channel: float) -> float:
    channel /= 255
    if channel <= 0.03928:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r_lin, g_lin, b_lin = (_srgb_to_linear(c) for c in (r, g, b))
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    lum_a = _relative_luminance(hex_a) + 0.05
    lum_b = _relative_luminance(hex_b) + 0.05
    return max(lum_a, lum_b) / min(lum_a, lum_b)


def test_ink_on_background_meets_aa_for_body_text():
    assert contrast_ratio(TOKENS["ink"], TOKENS["bg"]) >= 4.5


def test_soft_body_text_on_background_meets_aa():
    assert contrast_ratio(TOKENS["soft"], TOKENS["bg"]) >= 4.5


def test_mute_text_meets_aa_for_large_text_only():
    # --mute is "not for long paragraphs" -- held to the
    # large-text/UI-component threshold (3:1), not the body-text one (4.5:1).
    assert contrast_ratio(TOKENS["mute"], TOKENS["bg"]) >= 3.0


def test_accent_on_background_meets_aa():
    assert contrast_ratio(TOKENS["accent"], TOKENS["bg"]) >= 4.5


def test_background_on_accent_meets_aa_for_solid_buttons():
    assert contrast_ratio(TOKENS["bg"], TOKENS["accent"]) >= 4.5


def test_accent_hi_on_background_meets_aa():
    assert contrast_ratio(TOKENS["accent-hi"], TOKENS["bg"]) >= 4.5
