"""Generates tray icons (waveform + status badge) with Pillow."""

from __future__ import annotations

from PIL import Image, ImageDraw

from diktux.state import TrayStatus

BASE_ALPHA: dict[TrayStatus, list[float]] = {
    TrayStatus.IDLE: [1.0, 0.82, 0.64, 0.46],
    TrayStatus.RECORDING: [1.0, 0.42, 0.28, 0.18],
    TrayStatus.PROCESSING: [1.0, 0.84, 0.68, 0.52],
    TrayStatus.SUCCESS: [1.0, 0.9, 0.78, 0.62],
    TrayStatus.ERROR: [1.0, 0.7, 0.52, 0.36],
}

_RECORDING_FRAMES = [
    [1.0, 0.42, 0.28, 0.18],
    [0.82, 1.0, 0.4, 0.24],
    [0.58, 0.86, 1.0, 0.36],
    [0.4, 0.62, 0.88, 1.0],
]
_PROCESSING_FRAMES = [
    [1.0, 0.84, 0.68, 0.52],
    [0.92, 0.8, 0.64, 0.5],
    [0.84, 0.74, 0.6, 0.48],
    [0.92, 0.8, 0.64, 0.5],
]


def frame_count(status: TrayStatus) -> int:
    if status in (TrayStatus.RECORDING, TrayStatus.PROCESSING):
        return 4
    return 1


def _alpha_row(status: TrayStatus, frame: int) -> list[float]:
    if status is TrayStatus.RECORDING:
        return _RECORDING_FRAMES[frame % len(_RECORDING_FRAMES)]
    if status is TrayStatus.PROCESSING:
        return _PROCESSING_FRAMES[frame % len(_PROCESSING_FRAMES)]
    return BASE_ALPHA[status]


def _draw_waveform(draw: ImageDraw.ImageDraw, size: int, alphas: list[float]) -> None:
    widths = [0.66, 0.55, 0.44, 0.33]
    stripe_h = size * 0.11
    spacing = size * 0.09
    total = len(widths) * stripe_h + (len(widths) - 1) * spacing
    origin_y = (size - total) / 2
    for index, width_frac in enumerate(widths):
        width = size * width_frac
        x0 = (size - width) / 2
        y0 = origin_y + index * (stripe_h + spacing)
        alpha = int(max(0.0, min(1.0, alphas[index])) * 255)
        draw.rounded_rectangle(
            [x0, y0, x0 + width, y0 + stripe_h],
            radius=stripe_h / 2,
            fill=(0, 0, 0, alpha),
        )


def _badge_box(size: int) -> list[float]:
    badge = size * 0.42
    return [size - badge, size - badge, size - size * 0.04, size - size * 0.04]


def _draw_badge(draw: ImageDraw.ImageDraw, size: int, status: TrayStatus, frame: int) -> None:
    box = _badge_box(size)
    cx = (box[0] + box[2]) / 2
    cy = (box[1] + box[3]) / 2
    r = (box[2] - box[0]) / 2

    if status in (TrayStatus.SUCCESS, TrayStatus.ERROR):
        draw.ellipse(box, fill=(0, 0, 0, 255))
        if status is TrayStatus.SUCCESS:
            draw.line(
                [(cx - r * 0.4, cy), (cx - r * 0.05, cy + r * 0.4),
                 (cx + r * 0.5, cy - r * 0.4)],
                fill=(255, 255, 255, 255),
                width=max(1, int(size * 0.03)),
            )
        else:
            draw.line(
                [(cx, cy - r * 0.45), (cx, cy + r * 0.2)],
                fill=(255, 255, 255, 255),
                width=max(1, int(size * 0.04)),
            )
            draw.ellipse(
                [cx - r * 0.07, cy + r * 0.35, cx + r * 0.07, cy + r * 0.49],
                fill=(255, 255, 255, 255),
            )
    elif status is TrayStatus.RECORDING:
        draw.ellipse(box, fill=(0, 0, 0, 255))
    elif status is TrayStatus.PROCESSING:
        draw.ellipse(box, fill=(0, 0, 0, 200))
        orbit = [
            (cx, box[1] - r * 0.3),
            (box[2] + r * 0.3, cy),
            (cx, box[3] + r * 0.3),
            (box[0] - r * 0.3, cy),
        ]
        px, py = orbit[frame % len(orbit)]
        dot = r * 0.28
        draw.ellipse([px - dot, py - dot, px + dot, py + dot], fill=(0, 0, 0, 235))


def make_icon(status: TrayStatus, frame: int = 0, size: int = 64) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    _draw_waveform(draw, size, _alpha_row(status, frame))
    if status is not TrayStatus.IDLE:
        _draw_badge(draw, size, status, frame)
    return image
