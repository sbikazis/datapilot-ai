from visual_identity import (
    THEMES,
    build_theme_css,
    resolve_theme,
    theme_chart_colors,
    theme_chart_scale,
)


def test_automatic_theme_tracks_detected_domain():
    assert resolve_theme("Automatic · domain aware", "Finance & accounting")["label"] == "Executive"
    assert resolve_theme("Automatic · domain aware", "Customer & audience")["label"] == "Oceanic"
    assert resolve_theme("Automatic · domain aware", "Operations & service")["label"] == "Botanical"
    assert resolve_theme("Automatic · domain aware", "General / mixed data")["label"] == "Nebula"


def test_manual_theme_overrides_domain():
    assert resolve_theme("Heritage / archive", "Sales & commerce")["label"] == "Heritage"


def test_all_themes_have_light_and_dark_contrast_tokens():
    for theme in THEMES.values():
        for mode in ("light", "dark"):
            palette = theme[mode]
            for key in ("canvas", "surface", "text", "muted", "line", "accent", "sidebar", "sidebar_text"):
                assert palette[key].startswith("#")


def test_chart_palettes_are_distinct_and_appearance_aware():
    for theme in THEMES.values():
        light = theme_chart_colors(theme, "Light")
        dark = theme_chart_colors(theme, "Dark")
        assert len(light) >= 6
        assert len(set(light)) == len(light)
        assert len(dark) >= 6
        assert len(set(dark)) == len(dark)
        assert light != dark


def test_continuous_chart_scale_uses_the_active_appearance():
    theme = THEMES["Nebula / sci-fi"]
    assert theme_chart_scale(theme, "Light")[0] == theme["light"]["surface_2"]
    assert theme_chart_scale(theme, "Dark")[0] == theme["dark"]["surface_2"]
    assert theme_chart_scale(theme, "Dark")[-1] == theme["dark"]["accent"]


def test_theme_css_contains_responsive_interaction_and_accessibility_rules():
    css = build_theme_css(THEMES["Nebula / sci-fi"], "Dark", "Compact")
    assert "--canvas:#0d1020" in css
    assert "@media(max-width:768px)" in css
    assert "@media(max-width:480px)" in css
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert ":disabled" in css
    assert "stChatMessage" in css
    assert "stPlotlyChart" in css
    assert "__CANVAS__" not in css
    assert "color-scheme:dark" in css


def test_theme_gallery_renders_all_choices_and_marks_the_active_theme():
    from visual_identity import theme_gallery_html

    gallery = theme_gallery_html("Botanical / nature", "Operations & service")
    assert gallery.count('style="--preview-canvas:') == 5
    assert 'class="theme-preview is-selected"' in gallery
    assert "Botanical" in gallery
    assert "is-selected" in gallery
