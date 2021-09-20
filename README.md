# sprite-sheet-aligner

Quick and dirty project to "center" spritesheets so that when imported into a game engine, they have the correct centers off the bat when a simple grid based cut is used on the spritesheet.
This is intended for use on spritesheets that are already in a grid with a transparent background, but each individual sprite is not in the exact position in the grid.

## Requirements
- Pygame
- Numpy

## Usage
`python3 spritesheetaligner.py <png_file>`

First, the program will show you your spritesheet with red rectangles of where it thinks your sprites are.
Press the **c** key to continue.
The program will then show you each individual sprite. Click on the center of each sprite (the program will round it off to each pixel). Proceed until the end of the spritesheet, and a corrected file will be created.
