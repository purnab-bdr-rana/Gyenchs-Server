# Convert hex color to HSL
import colorsys

import colorsys
def hex_to_hsl(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360, s, l)  # Convert hue to degrees

# Return smallest difference between hues on the color wheel
def hue_difference(hue1, hue2):
    diff = abs(hue1 - hue2)
    return min(diff, 360 - diff)

# Get the most similar item by hue
def get_closest_item_by_hue(base_hex, items):
    try:
        base_hue, _, _ = hex_to_hsl(base_hex)
    except Exception:
        return None

    closest_item = None
    min_diff = float('inf')

    for item in items:
        try:
            hue, _, _ = hex_to_hsl(item.color)
            diff = hue_difference(base_hue, hue)
            if diff < min_diff:
                min_diff = diff
                closest_item = item
        except Exception:
            continue

    return closest_item