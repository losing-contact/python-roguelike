"""Тесты на правила слоёв: ломаются, если кто-то нарушит архитектуру."""
import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent


def python_files(layer: str):
    return sorted((SRC / layer).rglob("*.py"))


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("path", python_files("domain"), ids=lambda p: p.name)
def test_domain_does_not_depend_on_other_layers(path):
    forbidden = {"curses", "json", "presentation", "datalayer"}
    assert not imported_modules(path) & forbidden


@pytest.mark.parametrize("path", python_files("domain"), ids=lambda p: p.name)
def test_domain_has_no_global_random(path):
    """Случайность должна приходить через параметр rng, а не из модуля random."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id == "random" and node.attr != "Random"):
            pytest.fail(f"{path.name}:{node.lineno}: random.{node.attr} - используйте rng")


@pytest.mark.parametrize("path", python_files("datalayer"), ids=lambda p: p.name)
def test_datalayer_does_not_know_presentation(path):
    assert not imported_modules(path) & {"curses", "presentation"}


@pytest.mark.parametrize("path", python_files("presentation"), ids=lambda p: p.name)
def test_presentation_does_not_know_datalayer(path):
    assert "datalayer" not in imported_modules(path)
