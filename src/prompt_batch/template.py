"""Prompt template rendering.

Templates use Python's :mod:`string.Template` syntax, so ``$input`` is replaced
with each batch item. This keeps templates readable and dependency-free for
beginners while covering the common case of one prompt over many inputs.
"""

from __future__ import annotations

from string import Template


class TemplateError(Exception):
    """Raised when a template cannot be rendered."""


def render_template(template: str, input_text: str) -> str:
    """Render *template*, replacing ``$input`` with *input_text*."""
    try:
        return Template(template).substitute(input=input_text)
    except KeyError as exc:
        raise TemplateError(f"template references unknown variable: {exc}") from exc
    except ValueError as exc:
        raise TemplateError(f"malformed template: {exc}") from exc
