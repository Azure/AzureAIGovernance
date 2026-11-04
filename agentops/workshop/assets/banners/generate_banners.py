"""Draw the workshop's robot illustrations entirely offline.

The same sampled paths and text placements feed PNG, SVG and Excalidraw.
Run from the repository root with the interpreter documented in README.md.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import lru_cache
import hashlib
import io
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageChops, ImageDraw, ImageFont, PngImagePlugin


ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT, SCALE = 1200, 300, 4
FONT_DIR = Path(r"C:\Windows\Fonts")
FONT_FILES = {"regular": "comic.ttf", "bold": "comicbd.ttf"}
BG = "#f3f8fc"
NAVY = "#172b4d"
BLUE = "#0078d4"
LIGHT_BLUE = "#cfe4fa"
ORANGE = "#e77724"
LIGHT_ORANGE = "#fff0d3"
GREEN = "#23834b"
LIGHT_GREEN = "#dff3e5"
PURPLE = "#7351a2"
LIGHT_PURPLE = "#eae1f4"
PALE = "#d6e7f5"
WHITE = "#ffffff"
BLACK = "#000000"
NONE = "transparent"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


@dataclass(frozen=True)
class Banner:
    stem: str
    title: tuple[str, str]
    subtitle: str
    illustration: str


BANNERS = (
    Banner(
        "welcome",
        ("Build confidence.", "One agent step at a time."),
        "Evaluate, Ship, Observe and Operate with Microsoft Foundry.",
        "A smiling, blue-eyed robot waves beside three stepping stones and a star flag.",
    ),
    Banner(
        "prework",
        ("A little setup.", "More time to explore."),
        "Get your files ready, sign in, and bring your curiosity.",
        "The robot holds a sign-in key beside a folder of ready-to-use files.",
    ),
    Banner(
        "instructor",
        ("Set the stage.", "Let the learning happen."),
        "Prepare the essentials so the group can focus on the agent.",
        "The robot points to a learning route on an easel, with a clock and a checklist.",
    ),
    Banner(
        "evaluate",
        ("A good answer is a start.", "Check what the agent did."),
        "Test the help desk agent, inspect the results, and compare versions.",
        "The robot magnifies a three-step trace beside a clipboard of different test outcomes.",
    ),
    Banner(
        "ship",
        ("Check first.", "Then decide what ships."),
        "Review the checks and approvals that keep a release under control.",
        "The robot reviews a checklist beside a checkpoint barrier and a release package.",
    ),
    Banner(
        "observe-operate",
        ("Follow the clues.", "Choose the next move."),
        "Connect a slow or failed request to a clear response.",
        "The robot investigates a telemetry heartbeat, an alert and a magnified signal.",
    ),
    Banner(
        "advanced",
        ("Find the fault.", "Help it stay fixed."),
        "Review how an incident becomes a test that catches the same bug.",
        "The robot carries a wrench beside a bug, a repair loop and a regression-test card.",
    ),
    Banner(
        "host-setup",
        ("Meet your help desk agent.", "Give it a place to run."),
        "Prepare the two Foundry versions used throughout the workshop.",
        "The robot welcomes two numbered, connected agent hosts under a cloud.",
    ),
    Banner(
        "evidence",
        ("Every score has a story.", "Keep the right evidence."),
        "Open the files that show what was tested and what happened.",
        "The robot explores an open evidence folder, a chart, case records and a magnifier.",
    ),
    Banner(
        "tooling",
        ("Know your tools.", "Know their limits."),
        "Find the supported commands, versions and technical details here.",
        "The robot presents an open toolbox with a wrench, screwdriver, ruler and command card.",
    ),
    Banner(
        "criteria",
        ("Before testing everything,", "decide what good looks like."),
        "Choose the outcomes, risks, metrics, and tests that matter.",
        "The robot carries a clipboard and ruler beside a target, an orange dart and a check.",
    ),
    Banner(
        "ready-to-run",
        ("Ready to press Run?", "One run is enough to start."),
        "Cloud runs cost money. Check the results before trying again.",
        "The robot points toward one cloud Run button, with cost coins and a result slip.",
    ),
    Banner(
        "release-decision",
        ("Green is a clue,", "not a release decision."),
        "Check missing scores, failed cases and tool results before approval.",
        "The robot magnifies a release checklist with a pass, a failure and a missing result.",
    ),
)


@lru_cache(maxsize=None)
def font(size: float, face: str = "regular") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / FONT_FILES[face]), round(size * SCALE))


def advance(text: str, size: float, face: str = "regular") -> float:
    return font(size, face).getlength(text) / SCALE


def num(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


@dataclass
class Primitive:
    id: str
    kind: str
    groups: tuple[str, ...]
    layer: str
    points: list[tuple[float, float]] = field(default_factory=list)
    stroke: str = NAVY
    fill: str = NONE
    width: float = 3.4
    closed: bool = False
    text: str = ""
    x: float = 0
    baseline: float = 0
    size: float = 0
    face: str = "regular"
    leading: float = 0

    def bounds(self) -> tuple[float, float, float, float]:
        if self.kind == "text":
            boxes = []
            for index, line in enumerate(self.text.split("\n")):
                left, top, right, bottom = font(self.size, self.face).getbbox(
                    line, anchor="ls"
                )
                y = self.baseline + index * self.leading
                boxes.append(
                    (
                        self.x + left / SCALE,
                        y + top / SCALE,
                        self.x + right / SCALE,
                        y + bottom / SCALE,
                    )
                )
            return (
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            )
        pad = self.width / 2 if self.stroke != NONE else 0
        return (
            min(p[0] for p in self.points) - pad,
            min(p[1] for p in self.points) - pad,
            max(p[0] for p in self.points) + pad,
            max(p[1] for p in self.points) + pad,
        )


class Scene:
    def __init__(self, banner: Banner):
        self.banner = banner
        self.items: list[Primitive] = []
        self.groups: list[str] = []
        self.layer = "decoration"
        self.matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.serial = 0

    def identifier(self, name: str) -> str:
        self.serial += 1
        return f"{self.banner.stem}-{name}-{self.serial:03}"

    @contextmanager
    def group(self, name: str):
        self.groups.append(self.identifier(name))
        try:
            yield
        finally:
            self.groups.pop()

    @contextmanager
    def at(self, x: float, y: float, angle: float = 0, scale: float = 1):
        old = self.matrix
        a, b, c, d, e, f = old
        co, si = math.cos(math.radians(angle)) * scale, math.sin(math.radians(angle)) * scale
        self.matrix = (
            a * co + c * si,
            b * co + d * si,
            c * co - a * si,
            d * co - b * si,
            a * x + c * y + e,
            b * x + d * y + f,
        )
        try:
            yield
        finally:
            self.matrix = old

    def point(self, x: float, y: float) -> tuple[float, float]:
        a, b, c, d, e, f = self.matrix
        return round(a * x + c * y + e, 4), round(b * x + d * y + f, 4)

    def line(
        self,
        points: list[tuple[float, float]],
        color: str = NAVY,
        width: float = 3.4,
        fill: str = NONE,
        closed: bool = False,
    ):
        scale = math.hypot(self.matrix[0], self.matrix[1])
        transformed = [self.point(x, y) for x, y in points]
        # Make SVG's implicit fill closure explicit in every export.
        closed = closed or fill != NONE
        if closed and transformed[0] != transformed[-1]:
            transformed.append(transformed[0])
        self.items.append(
            Primitive(
                self.identifier("ink"),
                "path",
                tuple(self.groups),
                self.layer,
                points=transformed,
                stroke=color,
                fill=fill,
                width=round(width * scale, 4),
                closed=closed,
            )
        )

    def path(self, commands: str, fill: str = NONE, color: str = NAVY, width: float = 3.4):
        tokens = re.findall(r"[MLQCZ]|-?\d+(?:\.\d+)?", commands)
        index, points = 0, []
        current = (0.0, 0.0)
        while index < len(tokens):
            op = tokens[index]
            index += 1
            if op == "Z":
                self.line(points, color, width, fill, closed=True)
                points = []
                continue
            count = {"M": 2, "L": 2, "Q": 4, "C": 6}[op]
            args = [float(t) for t in tokens[index : index + count]]
            index += count
            end = tuple(args[-2:])
            if op == "M":
                if points:
                    self.line(points, color, width, fill)
                points = [end]
            elif op == "L":
                points.append(end)
            else:
                start = current
                steps = 16 if op == "C" else 12
                for step in range(1, steps + 1):
                    t = step / steps
                    u = 1 - t
                    if op == "Q":
                        p = tuple(
                            u * u * start[axis] + 2 * u * t * args[axis] + t * t * end[axis]
                            for axis in (0, 1)
                        )
                    else:
                        p = tuple(
                            u**3 * start[axis]
                            + 3 * u * u * t * args[axis]
                            + 3 * u * t * t * args[axis + 2]
                            + t**3 * end[axis]
                            for axis in (0, 1)
                        )
                    points.append(p)
            current = end
        if points:
            self.line(points, color, width, fill)

    def ellipse(
        self,
        x: float,
        y: float,
        rx: float,
        ry: float | None = None,
        fill: str = NONE,
        color: str = NAVY,
        width: float = 3.4,
        wobble: float = 0.012,
    ):
        ry = rx if ry is None else ry
        points = []
        for i in range(80):
            theta = 2 * math.pi * i / 80
            r = 1 + wobble * math.sin(3 * theta + 0.4) + wobble / 2 * math.cos(5 * theta)
            points.append((x + rx * r * math.cos(theta), y + ry * r * math.sin(theta)))
        self.line(points, color, width, fill, closed=True)

    def text(self, text: str, x: float, baseline: float, size: float, face: str = "regular", leading: float | None = None):
        a, b, _, _, _, _ = self.matrix
        if abs(b) > 0.0001:
            raise ValueError("Keep editable text unrotated; rotate the surrounding illustration instead.")
        x, baseline = self.point(x, baseline)
        self.items.append(
            Primitive(
                self.identifier("text"),
                "text",
                tuple(self.groups),
                self.layer,
                stroke=BLACK,
                fill=BLACK,
                width=0,
                text=text,
                x=x,
                baseline=baseline,
                size=size * a,
                face=face,
                leading=(leading or size * 1.35) * a,
            )
        )

    def fingerprint(self) -> str:
        data = json.dumps(
            {"background": BG, "size": [WIDTH, HEIGHT], "items": [vars(p) for p in self.items]},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(data.encode("ascii")).hexdigest()


def tick(s: Scene, x: float, y: float, size: float = 15, color: str = GREEN, width: float = 3.5):
    s.path(
        f"M {x - size * .48} {y} Q {x - size * .18} {y + size * .28} {x - size * .05} {y + size * .43} "
        f"L {x + size * .62} {y - size * .49}",
        color=color,
        width=width,
    )


def sparkle(s: Scene, x: float, y: float, size: float = 9, color: str = ORANGE):
    s.path(
        f"M {x} {y - size} Q {x + 1} {y - 1} {x + size * .72} {y} "
        f"Q {x + 1} {y + 1} {x} {y + size} Q {x - 1} {y + 1} {x - size * .72} {y} "
        f"Q {x - 1} {y - 1} {x} {y - size} Z",
        fill=color,
        color=color,
        width=1.4,
    )


def arrowhead(s: Scene, x: float, y: float, angle: float, color: str = BLUE, size: float = 8):
    with s.at(x, y, angle):
        s.line([(-size, -size * .55), (0, 0), (-size, size * .55)], color, 3)


def paper(s: Scene, x: float, y: float, scale: float = 1, angle: float = 0, accent: str = BLUE, check: bool = True):
    with s.group("paper"), s.at(x, y, angle, scale):
        s.path("M 1 2 L 37 0 L 50 13 L 49 68 L 0 69 Z", fill=WHITE, width=2.6)
        s.path("M 37 1 L 36 14 L 49 13", color=accent, width=2)
        if check:
            tick(s, 13, 29, 9, GREEN, 2.6)
            tick(s, 13, 45, 9, GREEN, 2.6)
            s.path("M 24 27 L 39 27 M 24 44 L 39 43 M 10 58 L 39 58", width=2)
        else:
            s.path("M 10 25 L 38 24 M 10 36 L 34 35 M 10 48 L 40 47 M 10 59 L 27 58", color=accent, width=2.2)


def clipboard(s: Scene, x: float, y: float, scale: float = 1, angle: float = 0, mixed: bool = False):
    with s.group("clipboard"), s.at(x, y, angle, scale):
        s.path("M 7 0 L 72 1 Q 81 1 80 10 L 79 111 Q 79 117 71 116 L 6 115 Q -1 115 0 107 L 0 8 Q 0 0 7 0 Z", fill=LIGHT_ORANGE, width=3)
        s.path("M 9 13 L 70 12 L 70 103 L 8 104 Z", fill=WHITE, color=NONE, width=0)
        s.path("M 27 -5 L 54 -4 Q 60 -4 59 3 L 57 13 L 23 12 L 22 3 Q 22 -4 27 -5 Z", fill=LIGHT_BLUE, width=2.7)
        s.path("M 11 17 L 11 96 M 16 104 L 64 103", color="#cfdbeb", width=1.7)
        for row, yy in enumerate((35, 62, 89)):
            s.ellipse(23, yy, 7, color=GREEN if row == 0 or not mixed else ORANGE if row == 1 else PURPLE, width=2)
            if mixed and row == 1:
                s.path(f"M 19 {yy - 4} L 27 {yy + 4} M 27 {yy - 4} L 19 {yy + 4}", color=ORANGE, width=2.5)
            elif mixed and row == 2:
                s.ellipse(23, yy, 1.6, fill=PURPLE, color=NONE, width=0)
            else:
                tick(s, 23, yy, 9, GREEN, 2.6)
            s.path(f"M 38 {yy - 3} L 61 {yy - 4} M 38 {yy + 4} L 55 {yy + 4}", width=2.1)


def folder(s: Scene, x: float, y: float, scale: float = 1, angle: float = 0, evidence: bool = False):
    with s.group("folder"), s.at(x, y, angle, scale):
        s.path("M 1 14 L 4 3 L 40 1 L 51 14 L 110 12 L 115 91 L 5 96 Z", fill=LIGHT_BLUE if evidence else LIGHT_ORANGE, width=3)
        paper(s, 15, -27, .94, -6, BLUE, not evidence)
        paper(s, 61, -37, .94, 8, PURPLE, True)
        if evidence:
            s.path("M 25 20 L 25 -2 M 25 19 L 46 18", width=1.8)
            s.path("M 27 14 L 33 7 L 39 11 L 45 -3", color=BLUE, width=2.5)
        s.path("M 5 39 L 113 35 Q 119 34 117 42 L 106 96 L 6 98 L -5 47 Q -6 40 5 39 Z", fill=LIGHT_ORANGE if evidence else LIGHT_BLUE, width=3.3)
        s.path("M 7 46 Q 55 42 108 43 M 14 87 L 57 86", color=ORANGE if evidence else BLUE, width=2)
        s.path("M 18 56 L 43 55 L 43 66 L 18 67 Z", fill=WHITE, color=NONE, width=0)
        s.path("M 22 61 L 38 60", width=1.8)


def magnifier(s: Scene, x: float, y: float, radius: float = 27, trace: bool = False):
    with s.group("magnifier"), s.at(x, y, scale=radius / 27):
        s.path("M -20 18 L -43 42 Q -46 47 -40 51 Q -36 53 -32 47 L -13 24 Z", fill=LIGHT_PURPLE, width=3)
        s.ellipse(0, 0, 27, fill=WHITE, width=3.5)
        s.ellipse(0, 0, 21, fill="#eaf5fc", color=BLUE, width=2)
        s.path("M -15 -10 Q -10 -18 -2 -18", color=WHITE, width=3.8)
        if trace:
            s.path("M -12 5 L 0 -4 L 12 4", color=BLUE, width=2.6)
            for xx, yy, fill in ((-12, 5, BLUE), (0, -4, ORANGE), (12, 4, GREEN)):
                s.ellipse(xx, yy, 3.7, fill=fill, color=WHITE, width=1.5)


def wrench(s: Scene, x: float, y: float, angle: float = 0, scale: float = 1):
    with s.group("wrench"), s.at(x, y, angle, scale):
        s.path(
            "M -5 24 L -8 -14 Q -20 -21 -16 -34 L -9 -43 L -8 -27 L 3 -24 "
            "L 11 -32 L 6 -45 Q 24 -36 16 -21 L 6 -14 L 7 24 Q 7 33 0 34 Q -7 34 -5 24 Z",
            fill=LIGHT_BLUE, width=3,
        )
        s.ellipse(0, 24, 3.1, fill=WHITE, width=2)
        s.path("M -1 -11 L 1 15", color=BLUE, width=1.8)


def robot(s: Scene, pose: str = "offer"):
    with s.group("robot"):
        s.path("M 122 233 L 121 251 L 136 252 L 140 232 M 164 233 L 168 250 L 183 248 L 182 230", fill=WHITE, width=3.6)
        s.path("M 120 249 Q 110 248 108 258 L 141 259 L 141 250 Z", fill=LIGHT_BLUE, width=3.5)
        s.path("M 168 248 L 185 246 Q 196 248 197 257 L 166 258 Z", fill=LIGHT_BLUE, width=3.5)
        s.path("M 112 257 L 137 257 M 171 256 L 192 255", color=BLUE, width=1.8)

        left = {
            "wave": "M 118 194 Q 92 207 79 191 L 63 167",
            "key": "M 118 196 Q 86 214 74 192 L 66 181",
        }.get(pose, "M 118 195 Q 95 215 78 203 L 68 198")
        right = {
            "inspect": "M 186 196 Q 211 214 232 185",
            "point": "M 187 195 Q 218 203 245 174",
            "wrench": "M 188 196 Q 211 212 241 189",
        }.get(pose, "M 187 194 Q 214 219 249 196")
        for arm in (left, right):
            s.path(arm, color=NAVY, width=10.2)
            s.path(arm, color=LIGHT_BLUE, width=5.3)
        joint_left = (95.25, 199.75) if pose == "wave" else (91, 204) if pose == "key" else (96.5, 207)
        joint_right = {
            "inspect": (210, 202.25),
            "point": (217, 193.75),
            "wrench": (212.75, 202.25),
        }.get(pose, (216, 207))
        s.ellipse(*joint_left, 5.4, fill=WHITE, width=2.6)
        s.ellipse(*joint_right, 5.4, fill=WHITE, width=2.6)
        hand_left = (63, 163) if pose == "wave" else (66, 180) if pose == "key" else (65, 198)
        hand_right = (232, 185) if pose == "inspect" else (245, 174) if pose == "point" else (241, 189) if pose == "wrench" else (251, 195)
        s.ellipse(*hand_left, 8.6, 9, fill=WHITE, width=3)
        s.ellipse(*hand_right, 8.2, 8.5, fill=WHITE, width=3)
        if pose == "wave":
            s.path("M 57 157 L 53 147 M 63 153 L 62 141 M 69 156 L 72 146", width=3.3)
            s.path("M 43 154 Q 35 143 41 132 M 80 143 Q 87 153 83 164", color=BLUE, width=2.2)
        elif pose == "point":
            s.path("M 248 169 L 257 160", width=3)

        s.path("M 136 168 L 136 185 L 164 185 L 163 167 Z", fill=WHITE, width=3)
        s.path("M 139 178 L 160 178", color=BLUE, width=2)
        s.path("M 127 183 Q 114 183 114 198 L 110 231 Q 108 241 121 243 L 182 241 Q 195 240 191 229 L 187 197 Q 186 183 175 183 Z", fill=LIGHT_BLUE, width=3.7)
        s.path("M 121 200 L 118 229 Q 119 235 126 235 L 145 235", color=WHITE, width=3.3)
        s.ellipse(151, 209, 13.2, fill=WHITE, color=BLUE, width=2.6)
        sparkle(s, 151, 209, 7.2, BLUE)
        for xx, color in ((145, PURPLE), (157, ORANGE), (169, GREEN)):
            s.ellipse(xx, 231, 2.7, fill=color, color=NONE, width=0)

        s.path("M 97 113 L 89 113 Q 83 115 84 122 L 85 138 Q 86 145 96 143 M 200 111 L 209 112 Q 215 113 214 121 L 213 135 Q 213 142 203 142", fill=LIGHT_BLUE, width=3.3)
        s.path("M 150 83 L 151 63", width=3.8)
        s.ellipse(151, 55, 7.7, fill=ORANGE, width=3)
        s.path("M 149 51 L 152 50", color=LIGHT_ORANGE, width=2)
        s.path(
            "M 96 103 Q 95 82 116 81 L 181 80 Q 203 82 204 103 L 203 151 "
            "Q 201 173 180 174 L 118 174 Q 95 171 95 152 Z",
            fill=WHITE, width=3.9,
        )
        s.path("M 105 105 Q 105 91 119 91 L 142 90", color=LIGHT_BLUE, width=3)
        s.path("M 196 151 Q 194 164 183 165", color=LIGHT_BLUE, width=3)
        s.path("M 121 107 Q 128 103 136 106 M 166 106 Q 173 102 180 106", width=2.2)
        for xx in (129, 174):
            s.ellipse(xx, 121, 7.8, 9, fill=BLUE, width=2.6, wobble=.007)
            s.ellipse(xx - 2, 118, 2, fill=WHITE, color=NONE, width=0)
        s.path("M 112 140 L 121 141 M 182 140 L 191 139", color=LIGHT_BLUE, width=3.8)
        s.path("M 131 148 Q 151 164 176 147", width=3.4)
        s.path("M 143 155 Q 150 158 158 155", color=BLUE, width=1.8)


def background(s: Scene):
    with s.group("paper-edge"):
        s.path("M 29 27 C 183 18 314 33 461 25 C 689 17 900 34 1170 24", color=PALE, width=2.2)
        s.path("M 29 277 C 198 286 335 269 495 279 C 711 287 933 269 1170 278", color=PALE, width=2.2)
        s.ellipse(220, 259, 173, 6.5, fill="#e2eef7", color=NONE, width=0, wobble=.01)
        s.path("M 51 111 C 62 80 97 64 118 71 M 210 66 Q 238 69 253 87", color="#dfedf8", width=2)
        for xx, yy, rr in ((42, 108, 2.1), (55, 92, 1.8), (218, 73, 2), (231, 81, 1.7), (400, 247, 2)):
            s.ellipse(xx, yy, rr, fill=PALE, color=NONE, width=0)
        s.path("M 419 115 L 427 112 M 418 131 L 429 134", color=ORANGE, width=2.7)


def welcome(s: Scene):
    robot(s, "wave")
    with s.group("small-steps"):
        for x, top, fill, accent in (
            (248, 222, LIGHT_BLUE, BLUE),
            (295, 194, LIGHT_GREEN, GREEN),
            (342, 165, LIGHT_PURPLE, PURPLE),
        ):
            s.path(f"M {x} {top + 3} L {x + 33} {top} L {x + 37} 246 L {x - 2} 247 Z", fill=fill, width=3)
            s.path(f"M {x + 5} {top + 10} L {x + 27} {top + 8}", color=accent, width=2)
        s.path("M 264 208 Q 276 189 288 181 M 309 178 Q 323 157 336 152", color=BLUE, width=2.4)
        arrowhead(s, 336, 152, -32, BLUE, 7)
        s.path("M 356 166 L 358 85", width=3.4)
        s.path("M 359 86 Q 377 78 394 92 L 388 118 Q 371 108 358 115 Z", fill=LIGHT_ORANGE, width=3)
        sparkle(s, 375, 98, 8, ORANGE)
        sparkle(s, 298, 115, 10, ORANGE)
        s.path("M 280 77 L 286 86 M 313 68 L 313 79", color=PURPLE, width=2.6)
        s.path("M 65 73 L 72 78 M 89 57 L 92 65", color=BLUE, width=2.4)


def prework(s: Scene):
    robot(s, "key")
    with s.group("sign-in-key"):
        s.ellipse(62, 158, 13, fill=LIGHT_ORANGE, width=3)
        s.ellipse(62, 158, 5, fill=BG, width=2.3)
        s.path("M 64 171 L 69 195 L 78 193 M 68 185 L 77 183", color=NAVY, width=5.5)
        s.path("M 64 172 L 69 194", color=ORANGE, width=2)
        sparkle(s, 44, 134, 7, ORANGE)
    folder(s, 276, 144, 1, -4)
    s.ellipse(321, 80, 21, fill=WHITE, color=GREEN, width=2.8)
    tick(s, 320, 80, 21, GREEN, 4)
    s.path("M 264 106 Q 276 95 288 97 M 270 100 L 264 106 L 271 109", color=PURPLE, width=2.5)


def instructor(s: Scene):
    robot(s, "point")
    clipboard(s, 47, 198, .49, -10)
    with s.group("learning-easel"):
        s.path("M 279 210 L 263 248 M 360 211 L 374 248 M 321 212 L 321 248", width=3.6)
        s.path("M 264 102 L 376 105 L 373 208 L 262 204 Z", fill=NONE, width=3.2)
        s.path("M 270 106 L 374 108", color=BLUE, width=2)
        s.path("M 257 209 Q 312 214 380 211", color=ORANGE, width=6)
        s.path("M 282 153 Q 301 129 317 155 Q 334 181 357 147", color=BLUE, width=2.5)
        for x, y, fill, accent in ((283, 154, LIGHT_BLUE, BLUE), (319, 154, LIGHT_ORANGE, ORANGE), (356, 150, LIGHT_GREEN, GREEN)):
            s.ellipse(x, y, 10, fill=fill, color=accent, width=2.4)
        tick(s, 356, 150, 10, GREEN, 2.8)
        s.path("M 282 126 L 321 125 M 282 188 L 298 188 M 316 188 L 333 189 M 351 188 L 361 188", width=2.1)
        s.path("M 249 171 L 287 129", width=2.6)
        s.ellipse(287, 128, 2.7, fill=ORANGE, color=NONE, width=0)
    with s.group("session-clock"):
        s.ellipse(350, 68, 21, fill=WHITE, width=2.8)
        s.path("M 350 54 L 350 68 L 361 72", color=BLUE, width=2.7)
        s.path("M 361 53 Q 370 59 370 68", color=ORANGE, width=2.6)
        s.ellipse(350, 68, 2.3, fill=NAVY, color=NONE, width=0)
    sparkle(s, 246, 76, 7, PURPLE)


def evaluate(s: Scene):
    robot(s, "inspect")
    clipboard(s, 294, 108, 1.03, -3, mixed=True)
    magnifier(s, 263, 149, 30, trace=True)
    paper(s, 46, 201, .55, -12, BLUE)
    s.path("M 302 83 Q 320 70 336 81 M 330 73 L 336 81 L 326 82", color=PURPLE, width=2.6)
    sparkle(s, 373, 79, 8, ORANGE)
    s.path("M 274 249 Q 293 240 309 247 Q 327 254 345 245", color=PURPLE, width=2.1)


def ship(s: Scene):
    robot(s)
    clipboard(s, 43, 197, .50, -12, mixed=True)
    with s.group("release-checkpoint"):
        s.path("M 269 150 L 267 245 L 282 245 L 281 151 Z", fill=LIGHT_BLUE, width=3)
        s.path("M 266 241 L 286 240 L 290 247 L 260 248 Z", fill=WHITE, width=2.7)
        s.path("M 275 151 L 375 116 L 380 127 L 278 162 Z", fill=LIGHT_ORANGE, width=3)
        for x, y in ((291, 146), (315, 138), (339, 130), (363, 122)):
            s.path(f"M {x} {y} L {x + 7} {y + 8}", color=ORANGE, width=4)
        s.ellipse(275, 157, 6, fill=WHITE, width=2.5)
        s.path("M 310 191 L 345 179 L 375 193 L 339 207 Z", fill=LIGHT_BLUE, width=2.9)
        s.path("M 310 191 L 312 231 L 340 244 L 339 207 Z", fill=WHITE, width=2.9)
        s.path("M 339 207 L 375 193 L 374 232 L 340 244 Z", fill=LIGHT_BLUE, width=2.9)
        s.path("M 325 186 L 354 200 L 354 219 L 365 214 L 365 197 L 337 182 Z", fill=LIGHT_PURPLE, color=PURPLE, width=1.8)
        s.path("M 318 214 L 331 220 M 318 220 L 330 226", color=BLUE, width=2)
        s.path("M 301 75 Q 321 72 338 78 L 336 101 Q 332 116 320 122 Q 305 116 301 102 Z", fill=LIGHT_GREEN, width=3)
        tick(s, 319, 96, 21, GREEN, 3.8)
    s.path("M 376 219 L 389 218 M 380 234 L 390 238", color=PURPLE, width=2.3)


def observe_operate(s: Scene):
    robot(s, "point")
    with s.group("telemetry-monitor"):
        s.path("M 265 109 Q 258 109 258 117 L 259 201 Q 259 208 266 208 L 384 205 Q 391 204 389 196 L 389 114 Q 389 108 381 108 Z", fill=NONE, width=3.5)
        s.path("M 263 116 L 383 115 M 263 196 L 385 194", color=LIGHT_BLUE, width=2)
        s.path("M 313 208 L 312 226 L 335 226 L 334 208 M 299 229 Q 322 223 347 228", width=3.1)
        s.path("M 271 160 L 286 160 L 293 150 L 302 177 L 315 130 L 326 164 L 337 155 L 346 159 L 376 157", color=BLUE, width=3.3)
        s.path("M 302 177 L 315 130 L 326 164", color=ORANGE, width=3.6)
        s.ellipse(315, 130, 4.2, fill=ORANGE, color=WHITE, width=1.8)
    with s.group("alert"):
        s.path("M 360 59 Q 363 52 367 59 L 386 88 Q 389 94 381 94 L 346 94 Q 340 94 345 88 Z", fill=LIGHT_ORANGE, width=2.8)
        s.path("M 364 67 L 364 78", color=BLACK, width=3)
        s.ellipse(364, 85, 1.7, fill=BLACK, color=NONE, width=0)
    magnifier(s, 369, 232, 19, trace=True)
    s.path("M 276 243 Q 292 237 307 242", color=PURPLE, width=2.3)
    sparkle(s, 66, 142, 8, PURPLE)


def advanced(s: Scene):
    robot(s, "wrench")
    wrench(s, 257, 161, 31, 1.1)
    with s.group("repair-loop"):
        s.path("M 282 111 C 301 76 354 85 371 112", color=BLUE, width=3.5)
        arrowhead(s, 372, 114, 53, BLUE, 9)
        s.path("M 379 132 C 392 161 373 191 349 198", color=GREEN, width=3.5)
        arrowhead(s, 347, 199, 165, GREEN, 9)
        s.path("M 325 199 C 298 197 282 184 277 165", color=PURPLE, width=3.3)
        arrowhead(s, 276, 163, -105, PURPLE, 8)
    with s.group("friendly-bug"):
        s.path("M 317 133 L 306 127 L 301 117 M 336 133 L 347 127 L 353 117 M 311 144 L 297 143 M 312 158 L 300 166 M 340 144 L 355 142 M 341 158 L 354 166", width=2.7)
        s.ellipse(327, 151, 18, 24, fill=LIGHT_PURPLE, width=3)
        s.ellipse(327, 128, 11, 9, fill=WHITE, width=2.6)
        s.path("M 321 120 L 316 112 M 332 120 L 337 111 M 327 138 L 328 171", width=2)
        for x, y in ((320, 145), (335, 153), (320, 162)):
            s.ellipse(x, y, 2.9, fill=PURPLE, color=NONE, width=0)
    with s.group("regression-test"):
        s.path("M 288 215 L 380 212 L 381 248 L 286 250 Z", fill=WHITE, width=2.8)
        s.path("M 296 230 L 305 236 L 312 223", color=GREEN, width=3.2)
        s.path("M 323 225 L 368 224 M 323 234 L 350 233 M 323 242 L 363 241", color=BLUE, width=2.2)
    sparkle(s, 68, 140, 7, ORANGE)


def host_setup(s: Scene):
    robot(s, "wave")
    with s.group("hosting-cloud"):
        s.path("M 265 133 C 242 130 244 105 263 101 C 257 76 291 69 303 87 C 315 56 355 65 359 93 C 385 83 407 109 390 127 Q 387 134 375 134", color=BLUE, width=3.1)
        s.path("M 289 96 Q 294 93 303 95", color=LIGHT_BLUE, width=2.5)
    with s.group("paired-agent-hosts"):
        s.path("M 294 224 L 293 245 L 357 245 L 357 224 M 322 245 L 322 254", color=BLUE, width=2.8)
        for x, fill, accent, label in ((266, LIGHT_BLUE, BLUE, "1"), (337, LIGHT_PURPLE, PURPLE, "2")):
            s.path(f"M {x + 4} 149 L {x + 47} 148 Q {x + 52} 148 {x + 52} 155 L {x + 51} 225 L {x} 225 L {x - 1} 156 Q {x - 1} 149 {x + 4} 149 Z", fill=WHITE, width=2.8)
            s.path(f"M {x} 198 L {x + 51} 197 L {x + 51} 224 L {x} 225 Z", fill=fill, color=accent, width=1.8)
            for xx in (x + 16, x + 34):
                s.ellipse(xx, 170, 3.5, fill=BLUE, color=NONE, width=0)
            s.path(f"M {x + 17} 183 Q {x + 25} 190 {x + 34} 182", width=2.1)
            s.text(label, x + 20, 216, 18, "bold")
        s.ellipse(322, 245, 3.7, fill=ORANGE, color=WHITE, width=1)
    sparkle(s, 254, 66, 7, ORANGE)


def evidence(s: Scene):
    robot(s)
    folder(s, 279, 151, 1, -3, evidence=True)
    paper(s, 45, 196, .57, -14, PURPLE, False)
    magnifier(s, 276, 225, 21, trace=True)
    with s.group("evidence-trail"):
        s.path("M 259 107 Q 271 94 288 99", color=PURPLE, width=2.3)
        for xx, yy in ((302, 88), (316, 84), (329, 83)):
            s.ellipse(xx, yy, 2.1, fill=BLUE, color=NONE, width=0)
        s.path("M 349 78 L 373 77 L 374 94 L 349 96 Z", fill=WHITE, width=2)
        s.path("M 354 84 L 368 83 M 354 89 L 364 89", color=PURPLE, width=1.8)
        sparkle(s, 388, 67, 6, ORANGE)


def tooling(s: Scene):
    robot(s, "wrench")
    with s.group("open-toolbox"):
        s.path("M 274 174 L 281 141 Q 282 137 288 137 L 369 140 Q 377 141 378 148 L 381 177 Z", fill=LIGHT_ORANGE, width=3.1)
        s.path("M 312 139 L 313 128 Q 313 123 320 123 L 338 124 Q 344 124 344 129 L 344 140", width=3.3)
        with s.at(290, 143, -8):
            s.path("M -6 -31 L 8 -31 L 10 52 L -6 52 Z", fill=LIGHT_PURPLE, width=2.8)
            for yy in (-23, -11, 1, 13, 25, 37):
                s.path(f"M -5 {yy} L 1 {yy}", color=PURPLE, width=1.8)
        with s.at(331, 151, 12):
            s.path("M -3 -28 L 4 -28 L 3 36 L -2 36 Z", fill=WHITE, width=2.4)
            s.path("M -8 -59 Q 0 -63 8 -57 L 7 -28 Q 0 -23 -7 -29 Z", fill=LIGHT_ORANGE, width=2.8)
            s.path("M 0 -54 L 0 -33", color=ORANGE, width=2)
        wrench(s, 362, 154, 17, .95)
        s.path("M 267 180 L 387 176 L 383 243 Q 327 250 270 243 Z", fill=LIGHT_BLUE, width=3.4)
        s.path("M 268 194 Q 324 199 385 191", color=BLUE, width=2.3)
        s.path("M 317 185 L 338 184 L 338 204 L 318 205 Z", fill=LIGHT_ORANGE, width=2.5)
        s.path("M 324 194 L 331 194 M 278 234 L 303 235", width=2)
    wrench(s, 253, 160, 25, .95)
    with s.group("command-card"):
        s.path("M 42 209 L 80 205 L 85 242 L 45 246 Z", fill=NONE, width=2.6)
        s.path("M 51 219 L 59 224 L 53 230 M 64 232 L 76 231", color=BLUE, width=2.5)
    sparkle(s, 279, 77, 8, ORANGE)


def criteria(s: Scene):
    robot(s)
    clipboard(s, 46, 193, .49, -13)
    with s.group("measure-and-aim"):
        with s.at(247, 197, -19):
            s.path("M -25 -9 L 33 -10 L 35 11 L -24 12 Z", fill=LIGHT_GREEN, width=2.9)
            for xx in (-16, -5, 6, 17, 28):
                s.path(f"M {xx} -8 L {xx} 2", color=GREEN, width=2)
        s.ellipse(336, 132, 49, fill=WHITE, width=3.4)
        s.ellipse(336, 132, 33, fill=LIGHT_BLUE, color=BLUE, width=2.8)
        s.ellipse(336, 132, 16, fill=WHITE, color=BLUE, width=2.8)
        s.ellipse(336, 132, 4, fill=ORANGE, color=NONE, width=0)
        s.path("M 336 132 L 286 84", color=NAVY, width=4.2)
        s.path("M 334 130 L 286 84", color=ORANGE, width=2.3)
        s.path("M 286 84 L 283 72 L 299 86 L 299 96 Z", fill=LIGHT_PURPLE, color=PURPLE, width=2.1)
        arrowhead(s, 336, 132, 44, ORANGE, 9)
        s.ellipse(365, 222, 22, fill=WHITE, color=GREEN, width=2.9)
        tick(s, 364, 222, 24, GREEN, 4.1)
        s.path("M 279 243 Q 298 232 317 242", color=PURPLE, width=2.4)
    sparkle(s, 382, 76, 7, ORANGE)


def ready_to_run(s: Scene):
    robot(s, "point")
    with s.group("one-cloud-run"):
        s.path("M 268 119 C 247 112 251 91 270 90 C 267 67 298 60 310 80 C 328 56 358 70 358 91 C 378 82 399 99 393 117", color=BLUE, width=2.9)
        s.ellipse(322, 154, 40, fill=WHITE, width=3.6)
        s.ellipse(322, 154, 32, fill=LIGHT_BLUE, color=BLUE, width=2)
        s.path("M 313 137 Q 312 134 316 137 L 340 151 Q 344 154 340 157 L 315 172 Q 311 174 312 169 Z", fill=BLUE, color=BLUE, width=2)
        s.path("M 296 207 Q 313 211 330 206", color=PURPLE, width=2.2)
    with s.group("cloud-cost"):
        s.path("M 274 230 L 274 243 Q 293 253 313 242 L 313 230 Z", fill=LIGHT_ORANGE, width=2.7)
        s.ellipse(293, 230, 19, 8, fill=LIGHT_ORANGE, width=2.7)
        s.path("M 278 239 Q 294 246 310 238 M 285 224 Q 293 221 302 225", color=ORANGE, width=2.1)
        s.ellipse(326, 238, 16, fill=LIGHT_ORANGE, width=2.6)
        s.ellipse(326, 238, 10, color=ORANGE, width=1.8)
        s.path("M 326 231 L 326 245", color=ORANGE, width=2)
    paper(s, 352, 195, .68, -4, BLUE, True)
    s.ellipse(372, 158, 13, fill=LIGHT_ORANGE, width=2.3)
    s.text("1", 368, 164, 18, "bold")
    sparkle(s, 67, 143, 7, ORANGE)


def release_decision(s: Scene):
    robot(s, "inspect")
    with s.group("release-review"):
        s.path("M 308 110 L 371 108 L 385 123 L 386 239 L 303 241 Z", fill=WHITE, width=3.2)
        s.path("M 370 110 L 369 124 L 383 123", color=BLUE, width=2.3)
        s.path("M 317 134 L 369 132", color=BLUE, width=3)
        for y, color in ((155, GREEN), (184, ORANGE), (213, PURPLE)):
            s.ellipse(324, y, 9, color=color, width=2.3)
            s.path(f"M 342 {y - 3} L 371 {y - 4} M 342 {y + 4} L 364 {y + 3}", width=2)
        tick(s, 324, 155, 12, GREEN, 3)
        s.path("M 320 180 L 328 188 M 328 180 L 320 188", color=ORANGE, width=2.8)
        s.text("?", 319, 219, 18, "bold")
        s.ellipse(308, 74, 16, fill=LIGHT_GREEN, color=GREEN, width=2.9)
        s.ellipse(308, 74, 7, fill=GREEN, color=NONE, width=0)
        s.path("M 323 79 Q 343 84 344 101", color=GREEN, width=2.6)
        arrowhead(s, 344, 101, 90, GREEN, 7)
    magnifier(s, 265, 151, 28, trace=True)
    with s.group("approval-stamp-at-rest"):
        s.path("M 269 230 L 295 232 L 300 244 L 264 241 Z", fill=LIGHT_ORANGE, width=2.7)
        s.path("M 276 230 L 278 218 Q 271 206 282 205 Q 293 207 286 219 L 285 231", fill=LIGHT_BLUE, width=2.7)
        s.path("M 266 247 L 298 250", color=PURPLE, width=2.6)
    sparkle(s, 379, 82, 7, ORANGE)


ILLUSTRATORS = {
    "welcome": welcome,
    "prework": prework,
    "instructor": instructor,
    "evaluate": evaluate,
    "ship": ship,
    "observe-operate": observe_operate,
    "advanced": advanced,
    "host-setup": host_setup,
    "evidence": evidence,
    "tooling": tooling,
    "criteria": criteria,
    "ready-to-run": ready_to_run,
    "release-decision": release_decision,
}


def build_scene(banner: Banner) -> Scene:
    s = Scene(banner)
    background(s)
    s.layer = "art"
    ILLUSTRATORS[banner.stem](s)
    s.layer = "copy"
    with s.group("headline"):
        s.text("\n".join(banner.title), 450, 103, 34, "bold", leading=46)
    with s.group("subtitle"):
        s.text(banner.subtitle, 450, 205, 21, leading=28)
    validate_scene(s)
    return s


def validate_scene(s: Scene):
    ids = [p.id for p in s.items]
    assert len(ids) == len(set(ids)), f"{s.banner.stem}: duplicate primitive IDs"
    copy_boxes = []
    for p in s.items:
        box = p.bounds()
        assert all(math.isfinite(v) for v in box), f"{p.id}: non-finite coordinates"
        assert box[0] >= 16 and box[1] >= 16 and box[2] <= WIDTH - 16 and box[3] <= HEIGHT - 16, (p.id, box)
        if p.layer == "art":
            assert box[2] <= 411, f"{p.id}: illustration intrudes into the copy gutter"
        if p.kind == "text":
            assert p.stroke == BLACK, f"{p.id}: text is not black"
        if p.layer == "copy":
            assert box[0] >= 450 and box[2] <= 1170, (p.id, box)
            copy_boxes.append(box)
            for first, second in zip(p.text.split("\n"), p.text.split("\n")[1:]):
                a = font(p.size, p.face).getbbox(first, anchor="ls")
                b = font(p.size, p.face).getbbox(second, anchor="ls")
                assert a[3] / SCALE + 8 <= p.leading + b[1] / SCALE, f"{p.id}: title lines touch"
    assert len(copy_boxes) == 2
    assert copy_boxes[0][3] + 20 <= copy_boxes[1][1], f"{s.banner.stem}: headline and subtitle touch"
    assert s.items[-2].text == "\n".join(s.banner.title)
    assert s.items[-1].text == s.banner.subtitle


def draw_png(s: Scene) -> Image.Image:
    image = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), BG)
    draw = ImageDraw.Draw(image)
    for p in s.items:
        if p.kind == "text":
            for index, line in enumerate(p.text.split("\n")):
                draw.text(
                    (round(p.x * SCALE), round((p.baseline + p.leading * index) * SCALE)),
                    line,
                    font=font(p.size, p.face),
                    fill=BLACK,
                    anchor="ls",
                )
        else:
            points = [(round(x * SCALE), round(y * SCALE)) for x, y in p.points]
            if p.closed and p.fill != NONE:
                draw.polygon(points, fill=p.fill)
            if p.stroke != NONE and p.width > 0:
                width = max(1, round(p.width * SCALE))
                draw.line(points, fill=p.stroke, width=width, joint="curve")
                radius = width / 2
                for x, y in (points[0], points[-1]):
                    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=p.stroke)
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def svg_tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


@lru_cache(maxsize=2)
def outline_font(face: str):
    return TTFont(str(FONT_DIR / FONT_FILES[face]))


@lru_cache(maxsize=None)
def glyph_path(face: str, character: str) -> str:
    tt = outline_font(face)
    glyphs = tt.getGlyphSet()
    glyph_name = tt.getBestCmap()[ord(character)]
    pen = SVGPathPen(glyphs)
    glyphs[glyph_name].draw(pen)
    return pen.getCommands()


def make_svg(s: Scene) -> str:
    root = ET.Element(
        svg_tag("svg"),
        {
            "width": str(WIDTH),
            "height": str(HEIGHT),
            "viewBox": f"0 0 {WIDTH} {HEIGHT}",
            "role": "img",
            "aria-labelledby": "title desc",
        },
    )
    ET.SubElement(root, svg_tag("title"), {"id": "title"}).text = " ".join(s.banner.title)
    ET.SubElement(root, svg_tag("desc"), {"id": "desc"}).text = f"{s.banner.subtitle} {s.banner.illustration}"
    ET.SubElement(root, svg_tag("metadata")).text = json.dumps(
        {"generator": "generate_banners.py", "source": f"{s.banner.stem}.excalidraw", "scene_sha256": s.fingerprint()},
        separators=(",", ":"),
    )
    defs = ET.SubElement(root, svg_tag("defs"))
    glyph_ids = {}
    for p in s.items:
        if p.kind == "text":
            for character in p.text:
                if character.isspace() or (p.face, character) in glyph_ids:
                    continue
                gid = f"glyph-{p.face}-{ord(character):04x}"
                glyph_ids[p.face, character] = gid
                ET.SubElement(defs, svg_tag("path"), {"id": gid, "d": glyph_path(p.face, character)})

    # This is the canvas color, not a filled diagram/container element.
    ET.SubElement(root, svg_tag("path"), {"d": f"M0 0H{WIDTH}V{HEIGHT}H0Z", "fill": BG, "aria-hidden": "true"})
    for p in s.items:
        if p.kind == "text":
            group = ET.SubElement(root, svg_tag("g"), {"id": p.id, "fill": BLACK, "aria-label": p.text})
            units = outline_font(p.face)["head"].unitsPerEm
            factor = p.size / units
            for index, line in enumerate(p.text.split("\n")):
                baseline = p.baseline + index * p.leading
                line_group = ET.SubElement(
                    group, svg_tag("g"),
                    {"transform": f"translate({num(p.x)} {num(baseline)}) scale({num(factor)} {num(-factor)})"},
                )
                for position, character in enumerate(line):
                    if character.isspace():
                        continue
                    origin = (advance(line[: position + 1], p.size, p.face) - advance(character, p.size, p.face)) / factor
                    ET.SubElement(
                        line_group, svg_tag("use"),
                        {"href": f"#{glyph_ids[p.face, character]}", "transform": f"translate({num(origin)} 0)"},
                    )
        else:
            points = p.points[:-1] if p.closed else p.points
            data = "M" + " L".join(f"{num(x)} {num(y)}" for x, y in points) + (" Z" if p.closed else "")
            ET.SubElement(
                root, svg_tag("path"),
                {
                    "id": p.id,
                    "d": data,
                    "fill": "none" if p.fill == NONE else p.fill,
                    "stroke": "none" if p.stroke == NONE else p.stroke,
                    "stroke-width": num(p.width),
                    "stroke-linecap": "round",
                    "stroke-linejoin": "round",
                },
            )
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def make_excalidraw(s: Scene) -> dict:
    def base(identifier, kind, x, y, width, height, groups=()):
        digest = hashlib.sha256(identifier.encode("ascii")).digest()
        return {
            "id": identifier,
            "type": kind,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "angle": 0,
            "strokeColor": NAVY,
            "backgroundColor": NONE,
            "fillStyle": "solid",
            "strokeWidth": 3,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": list(groups),
            "frameId": None,
            "roundness": None,
            "seed": int.from_bytes(digest[:4], "big") & 0x7fffffff,
            "version": 1,
            "versionNonce": int.from_bytes(digest[4:8], "big") & 0x7fffffff,
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
        }

    bounds = base(f"{s.banner.stem}-canvas", "rectangle", 0, 0, WIDTH, HEIGHT)
    bounds.update({"strokeColor": NONE, "opacity": 0, "locked": True, "strokeWidth": 1})
    elements = [bounds]
    for p in s.items:
        if p.kind == "text":
            lines = p.text.split("\n")
            width = (
                WIDTH - p.x - 26
                if p.layer == "copy"
                else math.ceil(max(advance(line, p.size, p.face) for line in lines) * 1.15 + 14)
            )
            height = math.ceil(p.size * 2.5 * len(lines))
            # Excalidraw's hand-drawn text uses a line-height based baseline.
            y = p.baseline - p.leading + p.size / 10
            element = base(p.id, "text", p.x, round(y, 4), width, height, p.groups)
            element.update(
                {
                    "strokeColor": BLACK,
                    "strokeWidth": 1,
                    "text": p.text,
                    "originalText": p.text,
                    "fontSize": p.size,
                    "fontFamily": 1,
                    "textAlign": "left",
                    "verticalAlign": "top",
                    "containerId": None,
                    "autoResize": False,
                    "lineHeight": p.leading / p.size,
                    "customData": {"exportFont": f"Comic Sans MS ({p.face})", "exportBaseline": p.baseline},
                }
            )
            assert element["x"] + width <= WIDTH - 16, f"{p.id}: editable text exceeds canvas width"
            assert y + height <= HEIGHT - 16, f"{p.id}: editable text exceeds canvas height"
        else:
            x = min(t[0] for t in p.points)
            y = min(t[1] for t in p.points)
            width = max(t[0] for t in p.points) - x
            height = max(t[1] for t in p.points) - y
            element = base(p.id, "line", x, y, round(width, 4), round(height, 4), p.groups)
            element.update(
                {
                    "strokeColor": p.stroke,
                    "backgroundColor": p.fill,
                    "strokeWidth": p.width,
                    "points": [[round(px - x, 4), round(py - y, 4)] for px, py in p.points],
                    "startBinding": None,
                    "endBinding": None,
                    "startArrowhead": None,
                    "endArrowhead": None,
                    "lastCommittedPoint": None,
                    "polygon": p.closed,
                }
            )
        elements.append(element)
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "agentops-workshop-banners",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": BG,
            "gridSize": None,
            "exportBackground": True,
            "exportWithDarkMode": False,
        },
        "files": {},
        "customData": {
            "canvas": [WIDTH, HEIGHT],
            "generator": "generate_banners.py",
            "scene_sha256": s.fingerprint(),
            "description": s.banner.illustration,
        },
    }


def encode_png(s: Scene, image: Image.Image) -> bytes:
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", " ".join(s.banner.title))
    metadata.add_text("Description", f"{s.banner.subtitle} {s.banner.illustration}")
    metadata.add_text("Source", f"{s.banner.stem}.excalidraw")
    metadata.add_text("SceneSHA256", s.fingerprint())
    output = io.BytesIO()
    image.save(output, format="PNG", pnginfo=metadata, optimize=True)
    return output.getvalue()


def validate_exports(s: Scene, expected_svg: str, expected_source: dict, expected_image: Image.Image):
    stem = ROOT / s.banner.stem
    raw_svg = stem.with_suffix(".svg").read_text(encoding="utf-8")
    xml = ET.fromstring(raw_svg)
    assert xml.attrib["viewBox"] == "0 0 1200 300"
    assert xml.attrib["width"] == "1200" and xml.attrib["height"] == "300"
    assert raw_svg == expected_svg, f"{s.banner.stem}: SVG does not match the scene"
    assert not list(xml.iter(svg_tag("image"))), "SVG must not depend on image files"
    xml_ids = [e.attrib["id"] for e in xml.iter() if "id" in e.attrib]
    assert len(xml_ids) == len(set(xml_ids)), "Duplicate SVG IDs"
    for element in xml.iter(svg_tag("use")):
        href = element.attrib["href"]
        assert href.startswith("#") and href[1:] in xml_ids, "Nonlocal or missing SVG glyph"
    for element in xml.iter(svg_tag("g")):
        if "aria-label" in element.attrib:
            assert element.attrib["fill"] == BLACK
    source = json.loads(stem.with_suffix(".excalidraw").read_text(encoding="utf-8"))
    assert source == expected_source, f"{s.banner.stem}: Excalidraw does not match the scene"
    assert source["type"] == "excalidraw" and source["version"] == 2
    ids = [e["id"] for e in source["elements"]]
    assert len(ids) == len(set(ids)), "Duplicate Excalidraw IDs"
    for element in source["elements"]:
        assert element["width"] >= 0 and element["height"] >= 0
        if element["type"] == "text":
            assert element["strokeColor"] == BLACK
            assert element["width"] > 0
            assert element["height"] >= element["fontSize"] * 2.5 * len(element["text"].split("\n"))
        if element["type"] == "rectangle":
            assert element["backgroundColor"] == NONE, "Diagram containers must be transparent"
    with Image.open(stem.with_suffix(".png")) as image:
        assert image.size == (WIDTH, HEIGHT) and image.mode == "RGB"
        assert image.info["SceneSHA256"] == s.fingerprint()
        assert ImageChops.difference(image, expected_image).getbbox() is None, "PNG does not match the scene"
        assert image.getpixel((0, 0)) == (243, 248, 252)
    return len(ids)


def contact_sheets():
    for page, start in enumerate(range(0, len(BANNERS), 4), 1):
        batch = BANNERS[start : start + 4]
        sheet = Image.new("RGB", (1240, 342 * len(batch) + 20), WHITE)
        draw = ImageDraw.Draw(sheet)
        qa_font = ImageFont.truetype(str(FONT_DIR / FONT_FILES["regular"]), 18)
        for row, banner in enumerate(batch):
            y = row * 342 + 12
            draw.text((22, y), banner.stem, font=qa_font, fill=BLACK)
            with Image.open(ROOT / f"{banner.stem}.png") as image:
                sheet.paste(image, (20, y + 27))
        sheet.save(ROOT / f".qa-contact-{page}.png", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing exports without rewriting them.")
    parser.add_argument("--contact-sheets", action="store_true", help="Write disposable .qa-contact-N.png review sheets here.")
    args = parser.parse_args()
    count = 0
    for banner in BANNERS:
        scene = build_scene(banner)
        svg = make_svg(scene)
        source = make_excalidraw(scene)
        image = draw_png(scene)
        stem = ROOT / banner.stem
        if not args.check:
            stem.with_suffix(".svg").write_text(svg, encoding="utf-8", newline="\n")
            stem.with_suffix(".excalidraw").write_text(json.dumps(source, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
            stem.with_suffix(".png").write_bytes(encode_png(scene, image))
        elements = validate_exports(scene, svg, source, image)
        count += elements
        print(f"OK {banner.stem}: 1200x300, {elements} editable elements, exact text, all exports aligned")
    if args.contact_sheets:
        contact_sheets()
        print("Review .qa-contact-1.png through .qa-contact-4.png; remove these review sheets afterward.")
    print(f"Verified {len(BANNERS)} banner triplets; {count} uniquely identified elements. No network access.")


if __name__ == "__main__":
    main()
