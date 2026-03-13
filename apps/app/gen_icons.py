import os
from PIL import Image, ImageDraw

def create_icon(filename, matrix, color_map, scale=4):
    img = Image.new('RGBA', (16*scale, 16*scale), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(matrix):
        for x, char in enumerate(row):
            if char in color_map:
                color = color_map[char]
                draw.rectangle([x*scale, y*scale, (x+1)*scale-1, (y+1)*scale-1], fill=color)
    img.save(filename)

monitor_mat = [
    "                ",
    " .............. ",
    " .............  ",
    " .##########..  ",
    " .#@@@@@@@@#..  ",
    " .#@@@@@@@@#..  ",
    " .#@@@@@@@@#..  ",
    " .#@@@@@@@@#..  ",
    " .##########..  ",
    " .###..###....  ",
    " .............  ",
    " .............. ",
    "    .####.      ",
    "  ..........    ",
    "  ..........    ",
    "                ",
]

floppy_mat = [
    "                ",
    "  ............  ",
    "  .#........#.  ",
    "  .##....###..  ",
    "  .##....###..  ",
    "  .##########.  ",
    "  .##########.  ",
    "  ...######...  ",
    "  .@.######.@.  ",
    "  .@.######.@.  ",
    "  .@.######.@.  ",
    "  .@@@@@@@@@@.  ",
    "  ............  ",
    "                ",
    "                ",
    "                ",
]

star_mat = [
    "                ",
    "       ..       ",
    "       ..       ",
    "      .##.      ",
    "      .##.      ",
    " ....######.... ",
    " .############. ",
    "  ...######...  ",
    "    .######.    ",
    "   .########.   ",
    "   .##....##.   ",
    "  .##.    .##.  ",
    "  ...      ...  ",
    "                ",
    "                ",
    "                ",
]

out_dir = r"d:\project\mcp-calculator\apps\app\static\tabs"
os.makedirs(out_dir, exist_ok=True)

idle_colors = {
    '.': '#424242', # outline
    '#': '#9E9E9E', # body
    '@': '#616161'  # screen/inner
}

active_colors = {
    '.': '#212121', # outline
    '#': '#D32F2F', # red body
    '@': '#FFCC00'  # yellow screen/inner
}

create_icon(os.path.join(out_dir, "home.png"), monitor_mat, idle_colors, 6)
create_icon(os.path.join(out_dir, "home-active.png"), monitor_mat, active_colors, 6)
create_icon(os.path.join(out_dir, "book.png"), floppy_mat, idle_colors, 6)
create_icon(os.path.join(out_dir, "book-active.png"), floppy_mat, active_colors, 6)
create_icon(os.path.join(out_dir, "trophy.png"), star_mat, idle_colors, 6)
create_icon(os.path.join(out_dir, "trophy-active.png"), star_mat, active_colors, 6)

print("Icons generated successfully.")
