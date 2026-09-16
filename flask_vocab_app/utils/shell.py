import re

from flask import render_template, request


def is_shell_navigation():
    """HTMX sidebar navigation swaps the main page shell, not inner fragments."""
    return request.headers.get("HX-Target") == "mainContent"


def extract_main_content(html):
    start = html.find('<main class="main-content" id="mainContent"')
    if start != -1:
        end = html.find("</main>", start)
        if end != -1:
            return html[start : end + len("</main>")]

    start = html.find('<div class="main-content" id="mainContent"')
    if start == -1:
        return html
    depth = 0
    for match in re.finditer(r"<(/?)div\b[^>]*>", html[start:], re.IGNORECASE):
        depth += -1 if match.group(1) else 1
        if depth == 0:
            return html[start : start + match.end()]
    return html


def render_page(template_name, **context):
    html = render_template(template_name, **context)
    if is_shell_navigation():
        return extract_main_content(html)
    return html
