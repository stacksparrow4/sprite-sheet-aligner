import pygame, sys
import numpy as np

pygame.init()

SCAN_SIZE = 2

SAMPLE_S_W = 640
SAMPLE_S_H = 640

MAX_COLS = 10

PADDING = 1

def flood_fill_rect_recurse(alpha, x,y, filled, rect):
    if filled[x,y] or alpha[x,y] == 0:
        return

    filled[x,y] = True

    if x < rect.left:
        rect.width += rect.left - x
        rect.left = x
    if x >= rect.right:
        rect.width += x + 1 - rect.right
        rect.right = x + 1
    if y < rect.top:
        rect.height += rect.top - y
        rect.top = y
    if y >= rect.bottom:
        rect.height += y + 1 - rect.bottom
        rect.bottom = y + 1

    for dx in range(-SCAN_SIZE, SCAN_SIZE+1):
        for dy in range(-SCAN_SIZE, SCAN_SIZE+1):
            if dx != 0 or dy != 0:
                flood_fill_rect_recurse(alpha, x+dx, y+dy, filled, rect)

def flood_fill_get_rect(alpha, x, y, filled):
    rect = pygame.rect.Rect(x,y,1,1)

    flood_fill_rect_recurse(alpha, x, y, filled, rect)

    return rect

def rect_contains(a, b):
    # a contains b
    return a.left <= b.left and a.top <= b.top and b.right <= a.right and b.bottom <= a.bottom

def order_rects_with_rows(rects):
    # First, find the rects that collide along the y axis
    rows = []
    for r in rects:
        found = False
        for candidate in rows:
            if abs(candidate[0].centery - r.centery) <= (candidate[0].height + r.height) / 2:
                candidate.append(r)
                found = True
                break
        if not found:
            rows.append([r])
            
    return rows

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <name_of_spritesheet_file>")
        exit(1)

    f_name = sys.argv[1]
    
    img_loaded = pygame.image.load(f_name)

    img = pygame.surfarray.array3d(img_loaded)
    alpha = pygame.surfarray.array_alpha(img_loaded)
    filled = np.zeros(shape=alpha.shape, dtype=bool)

    rects = []

    for x in range(0, img.shape[0]):
        for y in range(0, img.shape[1]):
            if alpha[x,y] != 0 and not filled[x,y]:
                # This is a coloured pixel. Try and find the containing rect.
                rects.append(flood_fill_get_rect(alpha, x, y, filled))

    # Remove all rects that are inside another rect
    dead_rects = []
    for a in rects:
        for b in rects:
            if b in dead_rects or a == b:
                continue
            if rect_contains(a, b):
                dead_rects.append(b)
    
    for r in dead_rects:
        rects.remove(r)

    rows = order_rects_with_rows(rects)
    
    # first, display all rects
    win = pygame.display.set_mode((img_loaded.get_width(), img_loaded.get_height()))

    debug_np = np.pad(np.expand_dims(filled * 255, axis=2), ((0,0), (0,0), (0,2)), mode="constant", constant_values=0)
    debug_surf = pygame.surfarray.make_surface(debug_np)

    mode_debug = False
    confirmed = False
    while not confirmed:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.display.quit()
                quit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_d:
                    mode_debug = not mode_debug
                elif e.key == pygame.K_c:
                    confirmed = True
            elif e.type == pygame.MOUSEBUTTONDOWN:
                print(e.pos)
        
        win.blit(img_loaded, (0,0))

        if not mode_debug:
            for row in rows:
                for r in row:
                    pygame.draw.rect(win, (255, 0, 0), (r.left - 1, r.top - 1, r.width + 2, r.height + 2), 1)
        else:
            win.blit(debug_surf, (0,0))

        pygame.display.update()
    
    pygame.display.quit()

    screen = pygame.display.set_mode((SAMPLE_S_W, SAMPLE_S_H))

    centers = []

    for row in rows:
        row_centers = []

        for r in row:
            subsurf = img_loaded.subsurface(r)

            use_width = r.width / r.height > SAMPLE_S_W / SAMPLE_S_H

            if use_width:
                scale_fac = SAMPLE_S_W / r.width
                x = 0
                y = (SAMPLE_S_H - r.height * scale_fac) // 2

                new_size = (SAMPLE_S_W, int(r.height * scale_fac))
            else:
                scale_fac = SAMPLE_S_H / r.height
                x = (SAMPLE_S_W - r.width * scale_fac) // 2
                y = 0

                new_size = (int(r.width * scale_fac), SAMPLE_S_H)

            screen.fill((0,0,0))
            screen.blit(pygame.transform.scale(subsurf, new_size), (x,y))

            done = False

            while not done:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        pygame.display.quit()
                        quit()
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        proper_x = round((e.pos[0] - x) / scale_fac)
                        proper_y = round((e.pos[1] - y) / scale_fac)

                        row_centers.append((proper_x, proper_y))
                        done = True

                        print(proper_x, proper_y)

                pygame.display.update()
        centers.append(row_centers)
    
    # Now, stitch all images into a spritesheet
    print("Stitching spritesheet...")

    # first calculate tile sizes (that can fit all tiles)
    sprite_max_top = 0
    sprite_max_bottom = 0
    sprite_max_left = 0
    sprite_max_right = 0

    for row_id, row in enumerate(rows):
        for r_id, r in enumerate(row):
            center = centers[row_id][r_id]

            top = center[1]
            bottom = r.height - center[1]
            left = center[0]
            right = r.width - center[0]

            if top > sprite_max_top:
                sprite_max_top = top
            if bottom > sprite_max_bottom:
                sprite_max_bottom = bottom
            if left > sprite_max_left:
                sprite_max_left = left
            if right > sprite_max_right:
                sprite_max_right = right
    
    tile_width = sprite_max_left + sprite_max_right + PADDING * 2
    tile_height = sprite_max_top + sprite_max_bottom + PADDING * 2

    tile_mid_x = tile_width // 2
    tile_mid_y = tile_height // 2

    # then blit all sprites onto a pygame surface
    x_tiles = max(*[len(r) for r in rows])
    y_tiles = len(rows)

    surf = pygame.Surface([x_tiles * tile_width, y_tiles * tile_height], pygame.SRCALPHA, 32)
    surf = surf.convert_alpha()

    for t_y, row in enumerate(rows):
        for t_x, r in enumerate(row):
            center = centers[t_y][t_x]

            blit_pos_x = t_x * tile_width + tile_mid_x - center[0]
            blit_pos_y = t_y * tile_height + tile_mid_y - center[1]

            surf.blit(img_loaded, (blit_pos_x, blit_pos_y), r)
    
    out_file_name = '.'.join(f_name.split('.')[:-1]) + '_stitched.png'
    pygame.image.save(surf, out_file_name)
    