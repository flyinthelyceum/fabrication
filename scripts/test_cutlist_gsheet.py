"""The cut-list Sheet sync never loses a student's entry."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cutlist_gsheet as C  # noqa: E402


def row(rid, kind="part", geom="600x400x18", cut=False, by="", note=""):
    return [cut, "p", "", "", by, "", False, note, "s1", "CNC", "", 1, rid, kind, geom]


def test_student_columns_survive_a_reorder():
    old = {"a": row("a", cut=True, by="Max Yin", note="clean"), "b": row("b")}
    out = C.merge([row("b"), row("a")], old)
    a = next(r for r in out if r[12] == "a")
    assert a[0] is True and a[4] == "Max Yin" and a[7] == "clean"


def test_size_change_after_cut_is_flagged():
    out = C.merge([row("a", geom="610x400x18")], {"a": row("a", cut=True)})
    assert out[0][14] == "cut at 600x400x18, model now 610x400x18"


def test_uncut_size_change_is_not_flagged():
    out = C.merge([row("a", geom="610x400x18")], {"a": row("a")})
    assert out[0][14] == "610x400x18"


def test_ticked_part_that_left_the_model_is_kept():
    old = {"gone": row("gone", cut=True, by="Max Yin"), "blank": row("blank")}
    ids = [r[12] for r in C.merge([row("a")], old)]
    assert "gone" in ids and "blank" not in ids
