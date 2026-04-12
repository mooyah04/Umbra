"""Generate custom textures for the Umbra addon."""

import math
from PIL import Image, ImageDraw, ImageFilter

PURPLE = (138, 43, 226)
TEX_DIR = "textures"


def generate_glow(size=512):
    """Intense radial glow — white-hot center fading to deep purple."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    center = size // 2

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy) / center

            if dist <= 1.0:
                if dist < 0.15:
                    alpha = 255
                    r, g, b = 255, 240, 255
                elif dist < 0.4:
                    t = (dist - 0.15) / 0.25
                    alpha = int(255 * (1.0 - t * 0.2))
                    r = int(255 - (255 - 180) * t)
                    g = int(240 - (240 - 80) * t)
                    b = int(255 - (255 - 255) * t)
                else:
                    t = (dist - 0.4) / 0.6
                    falloff = (1.0 - t) ** 1.8
                    alpha = int(200 * falloff)
                    r = int(160 * falloff)
                    g = int(50 * falloff)
                    b = int(255 * falloff)

                img.putpixel((x, y), (min(255, r), min(255, g), min(255, b), max(0, alpha)))

    img = img.filter(ImageFilter.GaussianBlur(radius=3))
    img.save(f"{TEX_DIR}/glow.tga")
    print(f"Generated glow.tga")


def generate_starburst(size=512, rays=16):
    """Sharp energy burst rays."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    center = size // 2

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy) / center

            if dist <= 1.0 and dist > 0.05:
                angle = math.atan2(dy, dx)
                ray1 = max(0, math.cos(angle * rays)) ** 4
                ray2 = max(0, math.cos(angle * rays * 0.5 + 0.5)) ** 6 * 0.5
                ray = ray1 + ray2
                fade = (1.0 - dist) ** 1.2
                center_boost = max(0, 1.0 - dist * 2) ** 0.5
                intensity = ray * fade + center_boost * 0.3
                alpha = int(min(255, 255 * intensity * 0.8))

                if alpha > 2:
                    brightness = min(1.0, intensity * 1.5)
                    r = int(140 + 115 * brightness)
                    g = int(40 + 100 * brightness)
                    b = int(200 + 55 * brightness)
                    img.putpixel((x, y), (min(255, r), min(255, g), min(255, b), alpha))

    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    img.save(f"{TEX_DIR}/starburst.tga")
    print(f"Generated starburst.tga")


def generate_ring(size=512, num_segments=24):
    """Arcane-style segmented ring."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    center = size // 2
    radius = center - 40
    thickness = 6

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)
            ring_dist = abs(dist - radius)
            angle = math.atan2(dy, dx)
            segment = math.cos(angle * num_segments)
            notch = 1.0 if segment > 0.3 else (0.4 if segment > -0.3 else 0.2)

            if ring_dist < thickness * 4:
                if ring_dist < thickness:
                    alpha = int(255 * notch)
                    brightness = (1.0 - ring_dist / thickness) * notch
                    r = int(180 + 75 * brightness)
                    g = int(80 + 80 * brightness)
                    b = int(240 + 15 * brightness)
                else:
                    falloff = (1.0 - (ring_dist - thickness) / (thickness * 3)) ** 2
                    alpha = int(120 * falloff * notch)
                    r = int(140 * falloff)
                    g = int(40 * falloff)
                    b = int(220 * falloff)

                if alpha > 1:
                    img.putpixel((x, y), (min(255, r), min(255, g), min(255, b), max(0, alpha)))

    inner_radius = radius - 18
    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)
            ring_dist = abs(dist - inner_radius)
            if ring_dist < 3:
                angle = math.atan2(dy, dx)
                dash = 1.0 if math.cos(angle * 36) > 0 else 0.3
                alpha = int(150 * (1.0 - ring_dist / 3) * dash)
                px = img.getpixel((x, y))
                new_a = min(255, px[3] + alpha)
                img.putpixel((x, y), (min(255, px[0] + 60), min(255, px[1] + 20), min(255, px[2] + 40), new_a))

    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    img.save(f"{TEX_DIR}/ring.tga")
    print(f"Generated ring.tga")


def generate_bar_pill(width=512, height=64):
    """Rounded pill-shaped bar fill texture with glossy highlight."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    radius = height // 2

    for x in range(width):
        for y in range(height):
            # Check if inside rounded rect (pill shape)
            inside = False
            if x < radius:
                # Left cap
                dx = x - radius
                dy = y - height // 2
                inside = (dx * dx + dy * dy) <= radius * radius
            elif x > width - radius:
                # Right cap
                dx = x - (width - radius)
                dy = y - height // 2
                inside = (dx * dx + dy * dy) <= radius * radius
            else:
                inside = True

            if inside:
                t = y / height
                # Glossy highlight on top third
                if t < 0.3:
                    highlight = (0.3 - t) / 0.3
                    brightness = 0.75 + 0.25 * highlight
                elif t > 0.75:
                    shadow = (t - 0.75) / 0.25
                    brightness = 0.65 - 0.15 * shadow
                else:
                    brightness = 0.70

                val = int(255 * brightness)
                img.putpixel((x, y), (val, val, val, 240))

    img.save(f"{TEX_DIR}/bar.tga")
    print(f"Generated bar.tga (pill)")


def generate_bar_bg_pill(width=512, height=64):
    """Dark rounded pill background for stat rows."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    radius = height // 2

    for x in range(width):
        for y in range(height):
            inside = False
            if x < radius:
                dx = x - radius
                dy = y - height // 2
                inside = (dx * dx + dy * dy) <= radius * radius
            elif x > width - radius:
                dx = x - (width - radius)
                dy = y - height // 2
                inside = (dx * dx + dy * dy) <= radius * radius
            else:
                inside = True

            if inside:
                t = y / height
                # Subtle inner shadow at top
                if t < 0.15:
                    val = 8
                    alpha = 240
                elif t > 0.85:
                    val = 12
                    alpha = 235
                else:
                    val = 18
                    alpha = 230

                img.putpixel((x, y), (val, val, val + 4, alpha))

    # Add a subtle 1px bright edge at the top for depth
    for x in range(radius, width - radius):
        px = img.getpixel((x, 1))
        if px[3] > 0:
            img.putpixel((x, 1), (50, 50, 60, 100))

    img.save(f"{TEX_DIR}/bar_bg.tga")
    print(f"Generated bar_bg.tga (pill)")


def generate_icon_ring(size=64):
    """Small circular frame for stat row icons."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    center = size // 2
    outer_r = center - 2
    inner_r = center - 5

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx * dx + dy * dy)

            # Dark filled circle
            if dist <= outer_r:
                if dist > inner_r:
                    # Ring edge — brighter
                    t = (dist - inner_r) / (outer_r - inner_r)
                    alpha = int(220 * (1.0 - t * 0.3))
                    val = int(80 + 40 * (1.0 - t))
                    img.putpixel((x, y), (val, val, val + 15, alpha))
                else:
                    # Dark interior
                    img.putpixel((x, y), (15, 12, 20, 200))

            # Outer glow
            elif dist <= outer_r + 3:
                falloff = 1.0 - (dist - outer_r) / 3
                alpha = int(60 * falloff)
                img.putpixel((x, y), (100, 50, 140, alpha))

    img.save(f"{TEX_DIR}/icon_ring.tga")
    print(f"Generated icon_ring.tga")


if __name__ == "__main__":
    generate_glow(512)
    generate_starburst(512)
    generate_ring(512)
    generate_bar_pill(512, 64)
    generate_bar_bg_pill(512, 64)
    generate_icon_ring(64)
    print("\nAll textures generated!")
