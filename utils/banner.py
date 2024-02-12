from PIL import Image, ImageOps

colors = {
    "WHITE": "#FFFFFF",
    "ORANGE": "#D87F33",
    "MAGENTA": "#B24CD8",
    "LIGHT_BLUE": "#6699D8",
    "YELLOW": "#E5E533",
    "LIME": "#7FCC19",
    "PINK": "#F27FA5",
    "GRAY": "#4C4C4C",
    "LIGHT_GRAY": "#999999",
    "SILVER": "#999999",
    "CYAN": "#4C7F99",
    "PURPLE": "#7F3FB2",
    "BLUE": "#334CB2",
    "BROWN": "#664C33",
    "GREEN": "#667F33",
    "RED": "#993333",
    "BLACK": "#191919"
}

_pattern_map = {
    "BASE": "base",
    "BORDER": "border",
    "BRICKS": "bricks",
    "CIRCLE": "circle",
    "CIRCLE_MIDDLE": "circle",  # Wynn api uses this
    "CREEPER": "creeper",
    "CROSS": "cross",
    "CURLY_BORDER": "curly_border",
    "DIAGONAL_LEFT": "diagonal_left",
    "DIAGONAL_RIGHT": "diagonal_right",
    "DIAGONAL_UP_LEFT": "diagonal_up_left",
    "DIAGONAL_LEFT_MIRROR": "diagonal_up_left",  # Wynn api uses this
    "DIAGONAL_UP_RIGHT": "diagonal_up_right",
    "DIAGONAL_RIGHT_MIRROR": "diagonal_up_right",  # Wynn api uses this
    "FLOWER": "flower",
    "GLOBE": "globe",
    "GRADIENT": "gradient",
    "GRADIENT_UP": "gradient_up",
    "HALF_HORIZONTAL": "half_horizontal",
    "HALF_HORIZONTAL_BOTTOM": "half_horizontal_bottom",
    "HALF_HORIZONTAL_MIRROR": "half_horizontal_bottom",  # Wynn api uses this
    "HALF_VERTICAL": "half_vertical",
    "HALF_VERTICAL_RIGHT": "half_vertical_right",
    "HALF_VERTICAL_MIRROR": "half_vertical_right",  # Wynn api uses this
    "MOJANG": "mojang",
    "PIGLIN": "piglin",
    "RHOMBUS": "rhombus",
    "RHOMBUS_MIDDLE": "rhombus",  # Wynn api uses this
    "SKULL": "skull",
    "SMALL_STRIPES": "small_stripes",
    "STRIPE_SMALL": "small_stripes",  # Wynn api uses this
    "SQUARE_BOTTOM_LEFT": "square_bottom_left",
    "SQUARE_BOTTOM_RIGHT": "square_bottom_right",
    "SQUARE_TOP_LEFT": "square_top_left",
    "SQUARE_TOP_RIGHT": "square_top_right",
    "STRAIGHT_CROSS": "straight_cross",
    "STRIPE_BOTTOM": "stripe_bottom",
    "STRIPE_CENTER": "stripe_center",
    "STRIPE_DOWNLEFT": "stripe_downleft",
    "STRIPE_DOWNRIGHT": "stripe_downright",
    "STRIPE_LEFT": "stripe_left",
    "STRIPE_MIDDLE": "stripe_middle",
    "STRIPE_RIGHT": "stripe_right",
    "STRIPE_TOP": "stripe_top",
    "TRIANGLE_BOTTOM": "triangle_bottom",
    "TRIANGLE_TOP": "triangle_top",
    "TRIANGLES_BOTTOM": "triangles_bottom",
    "TRIANGLES_TOP": "triangles_top",
}


def _colorize_image(src: Image.Image, color="#FFFFFF"):
    src = src.convert("LA")
    alpha = src.split()[-1]
    src = src.convert("L")
    result = ImageOps.colorize(src, (0, 0, 0, 0), color)
    result.putalpha(alpha)
    return result


def create_banner(base_color: str, layers: list[tuple[str, str]]) -> Image:
    """
    Create a banner with the given patterns.

    :param layers: A list of tuples in the format (color, pattern) to be used in the banner.
    """
    base = Image.open("assets/banner/base.png")
    banner = _colorize_image(base, colors[base_color])
    for color, pattern in layers:
        layer_color = _colorize_image(base, colors[color])
        mask = Image.open(f"assets/banner/{_pattern_map[pattern]}.png")

        banner = Image.composite(layer_color, banner, mask)

    return banner
