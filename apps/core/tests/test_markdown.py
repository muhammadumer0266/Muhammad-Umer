from apps.core.markdown import render_markdown


def test_render_markdown_produces_expected_html():
    result = render_markdown("Some *text*.")

    assert "<em>text</em>" in result


def test_render_markdown_demotes_h1_to_h2_so_page_title_stays_sole_h1():
    result = render_markdown("# Heading")

    assert "<h1>" not in result
    assert "<h2>Heading</h2>" in result


def test_render_markdown_demotes_all_heading_levels_without_double_shifting():
    result = render_markdown("# One\n\n## Two\n\n##### Five")

    assert "<h2>One</h2>" in result
    assert "<h3>Two</h3>" in result
    assert "<h6>Five</h6>" in result


def test_render_markdown_strips_disallowed_script_tags():
    result = render_markdown("Hello<script>alert(1)</script>")

    assert "<script>" not in result
    assert "alert" not in result


def test_render_markdown_handles_empty_text():
    assert render_markdown("") == ""
