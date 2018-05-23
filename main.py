# TODO: Warrior Toggle, Sex Toggle (Male, Female, None), Die Button
# TODO: Add to combat button (Starts combat if not already started
# TODO: Add min roll next to speed
# TODO: Highlight epic/winners
# TODO: Sounds
# TODO: Save/Load
# TODO: Connect from multiple comps (server/client) for graham's laptop on other end of table
# TODO: Select stats to ignore in combat (fight only with level, etc)

import random
import ctypes
import bisect
from ctypes import windll

import pygame

pygame.init()

# Constants Initialization

# RESOLUTION STUFF
DEFAULT_RESOLUTION = (1000, 750)
old_resolution = DEFAULT_RESOLUTION
# Get actual resolution including zoom
ctypes.windll.user32.SetProcessDPIAware()
TRUE_RES = (
    windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1))
# Find closest compatible resolution
RESOLUTIONS = [(1024, 768), (1280, 800), (1366, 768), (1280, 1024),
               (1920, 1080)]
res_sizes = list(x * y for (x, y) in RESOLUTIONS)
true_res_size = TRUE_RES[0] * TRUE_RES[1]
res_ind = bisect.bisect(res_sizes, true_res_size)
if res_ind == 0:
    res_ind = 1
true_res_compatible = RESOLUTIONS[res_ind - 1]

fullscreen = False

BACKGROUND_COLOR = (60, 63, 65)
DEFAULT_PLAYER_COLOR = (30, 35, 42)
POSITIVE_BUTTON_COLOR = (165, 225, 56)
NEGATIVE_BUTTON_COLOR = (248, 38, 114)
DEFAULT_BORDER_COLOR = (52, 54, 56)
COMBAT_STRENGTH_COLOR = (214, 150, 33)
STAT_COLOR = (255, 255, 255)
LEVEL_COLOR = (102, 216, 238)
BORDER_WIDTH = 3
DEFAULT_TEXT_COLOR = (255, 255, 255)
DEFAULT_FONT = "fredokaone, couriernew"

PLAYER_WIDTH = 250
BUTTON_WIDTH = 50
MARGIN = BUTTON_WIDTH * 2
player_height = PLAYER_WIDTH * 1.50
player_quarter = player_height / 4
min_window_width = (PLAYER_WIDTH + MARGIN) * 2 + MARGIN * 2

monster_mode = False

WINDOW_CAPTION = "Munchkin Level Counter"

PLAYER_BUTTON_NAMES = ["Level", "Gear", "1Shot", "Misc", "Speed"]
COMBAT_COMPONENTS = PLAYER_BUTTON_NAMES[:-1]


# Pygame Functions

def display_text(text, pos, color, _size):
    font = pygame.font.SysFont(DEFAULT_FONT, _size)
    label = font.render(text, 1, color)
    display.blit(label, pos)


def get_text_dimensions(text, _size):
    font = pygame.font.SysFont(DEFAULT_FONT, _size)
    return font.size(text)


def get_text_size_to_fit(text, rect):
    """Determines the largest size of text that will fit within rect"""
    _size = 0
    while True:
        text_dims = get_text_dimensions(text, _size)
        if text_dims[0] <= rect[2]:
            if text_dims[1] <= rect[3]:
                _size += 1
            else:
                break
        else:
            break

    return _size - 1


# Player Initialization

class Player:

    def __init__(self, name):
        self.name = name
        self.color = DEFAULT_PLAYER_COLOR
        self.name_rect = None
        self.name_size = None

        # Add player buttons
        self.buttons = [Button("Remove", "X", NEGATIVE_BUTTON_COLOR)]

        for button_name in PLAYER_BUTTON_NAMES:
            self.buttons.append(
                Button(button_name + " Up", "+", POSITIVE_BUTTON_COLOR))
            self.buttons.append(
                Button(button_name + " Down", "-", NEGATIVE_BUTTON_COLOR))

        self.rect = None
        self.naming = False
        self.name_pos = None

        self.levels = {}
        self.level_sizes = {}  # Stat value
        self.stat_sizes = {}  # Stat name
        for stat in PLAYER_BUTTON_NAMES:
            self.levels[stat] = 0 if stat != "Level" else 1
            self.level_sizes[stat] = None
            self.stat_sizes[stat] = None

        self.combat_strength = None
        self.combat_strength_pos = None
        self.combat_strength_size = None

    def render(self, player_rect):
        # Draw player box
        pygame.draw.rect(display, self.color, player_rect)
        pygame.draw.rect(display, DEFAULT_BORDER_COLOR, player_rect,
                         BORDER_WIDTH)

        # Determine name position and size and draw
        # Name is only a quarter of rect vertically
        self.rect = player_rect
        self.name_rect = player_rect[:3] + (player_quarter,)
        if isinstance(self.name_size, type(None)):
            minus_border_rect = list(self.name_rect)
            minus_border_rect[0] += BORDER_WIDTH
            minus_border_rect[2] -= BORDER_WIDTH
            minus_border_rect[1] += BORDER_WIDTH
            self.name_size = get_text_size_to_fit(self.name, minus_border_rect)
            self.name_pos = None

        # Display player name
        if isinstance(self.name_pos, type(None)):
            name_width = get_text_dimensions(self.name, self.name_size)[0]
            name_rect_half_width = (player_rect[0] + player_rect[2] / 2)
            self.name_pos = (
                name_rect_half_width - name_width / 2, player_rect[1])
        display_text(self.name, self.name_pos, DEFAULT_TEXT_COLOR,
                     self.name_size)

        # Display combat strength
        if isinstance(self.combat_strength, type(None)):
            self.combat_strength = sum(
                self.levels[stat] if stat in COMBAT_COMPONENTS else 0 for
                stat in self.levels)  # Only sum components to combat strength
            x = self.rect[0] - (MARGIN / 2)
            y = self.rect[1] - (MARGIN / 2)
            self.combat_strength_pos = (x, y)
            combat_strength_rect = self.combat_strength_pos + (
                MARGIN, MARGIN)
            self.combat_strength_size = get_text_size_to_fit(
                str(self.combat_strength), combat_strength_rect)
        display_text(str(self.combat_strength),
                     self.combat_strength_pos + (MARGIN, MARGIN),
                     COMBAT_STRENGTH_COLOR, self.combat_strength_size)

        # Display each level name and buttons
        stat_num = 0
        for button in self.buttons:
            pos = button.render()
            if not isinstance(pos, type(None)):
                x, y = pos
                x += BUTTON_WIDTH
                if "Down" in button.name:
                    # Render text
                    stat = PLAYER_BUTTON_NAMES[stat_num]
                    level = str(self.levels[stat])
                    stat_rect = (
                        x, y, PLAYER_WIDTH - BUTTON_WIDTH * 3, BUTTON_WIDTH)
                    level_rect = (
                        stat_rect[0] + stat_rect[2] + BUTTON_WIDTH / 2,
                        stat_rect[1], BUTTON_WIDTH, BUTTON_WIDTH)
                    if isinstance(self.stat_sizes[stat], type(None)):
                        self.stat_sizes[stat] = get_text_size_to_fit(stat,
                                                                     stat_rect)
                        self.level_sizes[stat] = get_text_size_to_fit(
                            level, level_rect)
                    display_text(stat, stat_rect[:2], STAT_COLOR,
                                 self.stat_sizes[stat])
                    display_text(level, level_rect[:2], LEVEL_COLOR,
                                 self.level_sizes[stat])
                    # Render level

                    stat_num += 1

        if self.naming:
            self.check_name()

    def check_name(self):
        global text_input
        self.name = text_input
        if "\r" in self.name:
            self.name = self.name[:self.name.index("\r")]
            reset_text_input()
            self.naming = False
        self.name_size = None

    def check_buttons(self):
        global last_click

        if not isinstance(last_click, type(None)):
            for _button in self.buttons:
                if _button.check(last_click):
                    if "Up" in _button.name:
                        stat_name = _button.name[:_button.name.index(" ")]
                        self.stat_sizes[stat_name] = None
                    self.combat_strength = None
                    last_click = None
                    if _button.name == "Remove":
                        players.remove(self)
                        resize_display()
                    else:
                        modifier = 1
                        if "Down" in _button.name:
                            modifier = -1
                        stat = _button.name[:_button.name.index(" ")]
                        if stat in self.levels:
                            self.levels[stat] += modifier
                        else:
                            raise Exception("Button '" + _button.name
                                            + "' does not have a function "
                                              "configured.")
                    break
        # Recheck in case a button was pressed
        if not isinstance(last_click, type(None)):
            self.naming = False
            if self.name_rect[0] <= last_click[0] <= self.name_rect[0] + \
                    self.name_rect[2]:
                if self.name_rect[1] <= last_click[1] <= self.name_rect[1] + \
                        self.name_rect[3]:
                    last_click = None
                    clear_naming_players()
                    self.naming = True
                    reset_text_input()

    def reset_buttons(self):
        for _button in self.buttons:
            x, y, w, h = None, None, BUTTON_WIDTH, BUTTON_WIDTH

            # Determine x pos
            if _button.name == "Remove" or "Up" in _button.name:
                x = (self.rect[0] + self.rect[2]) - (BUTTON_WIDTH / 2)
            else:
                x = self.rect[0] - (BUTTON_WIDTH / 2)

            # Determine y pos
            if _button.name == "Remove":
                y = self.rect[1] - BUTTON_WIDTH / 2
            else:
                y_level = PLAYER_BUTTON_NAMES.index(
                    _button.name[:_button.name.index(" ")])
                button_area = (player_height - player_quarter - BUTTON_WIDTH)
                total_button_height = (BUTTON_WIDTH * len(PLAYER_BUTTON_NAMES))
                button_margin = (button_area - total_button_height) / len(
                    PLAYER_BUTTON_NAMES)
                y = y_level * (BUTTON_WIDTH + button_margin)
                y += self.rect[1] + player_quarter
            button_rect = (x, y, w, h)
            if isinstance(button_rect[0], type(None)):
                raise Exception("Player button '" + _button.name
                                + "' does not have a position configured.")
            _button.pos = None
            _button.render(button_rect)


def clear_naming_players():
    for player in players:
        player.naming = False


def get_player_rect(player_num, button=False):
    # Find number of players that fit on a line
    players_per_line = len(players)
    if button:
        players_per_line += 1
    while True:
        line_players_width = (players_per_line * PLAYER_WIDTH)
        line_margins_width = (MARGIN * players_per_line) + MARGIN
        if line_players_width + line_margins_width > player_window_rect[2]:
            players_per_line -= 1
        else:
            break

    if players_per_line <= 0:
        raise Exception("Player width is too large")

    y, x = divmod(player_num, players_per_line)
    x *= (PLAYER_WIDTH + MARGIN)
    x += MARGIN
    y *= (player_height + MARGIN)
    y += MARGIN

    if button:
        _button_rect = list(i for i in range(0, 4))
        _button_rect[0] = x + ((PLAYER_WIDTH / 2) - (BUTTON_WIDTH / 2))
        _button_rect[1] = (y + player_height / 2) - (BUTTON_WIDTH / 2)
        _button_rect[2], _button_rect[3] = BUTTON_WIDTH, BUTTON_WIDTH
        return _button_rect

    return x, y, PLAYER_WIDTH, player_height


class Button:

    def __init__(self, name, text, text_color=POSITIVE_BUTTON_COLOR,
                 color=DEFAULT_PLAYER_COLOR):
        self.name = name
        self.text = text
        self.text_color = text_color
        self.color = color

        self.text_size = None
        self.rect = None

        self.pos = None

    def render(self, rect=None):
        if isinstance(rect, type(None)):
            if not isinstance(self.rect, type(None)):
                rect = self.rect
            else:
                return None  # If player has not yet been rendered, skip
        else:
            self.rect = rect
        pygame.draw.rect(display, self.color, rect)
        pygame.draw.rect(display, DEFAULT_BORDER_COLOR, rect, BORDER_WIDTH)

        if isinstance(self.text_size, type(None)):
            self.pos = None
            minus_border_rect = list(rect)
            minus_border_rect[0] += BORDER_WIDTH
            minus_border_rect[1] += BORDER_WIDTH
            minus_border_rect[2] -= BORDER_WIDTH
            minus_border_rect[3] -= BORDER_WIDTH

            self.text_size = get_text_size_to_fit(self.text, minus_border_rect)

        if isinstance(self.pos, type(None)):
            half_width = rect[0] + rect[2] / 2
            half_height = rect[1] + rect[3] / 2
            text_dims = get_text_dimensions(self.text, self.text_size)
            x = half_width - text_dims[0] / 2
            y = half_height - text_dims[1] / 2
            self.pos = [x, y]
        display_text(self.text, self.pos, self.text_color, self.text_size)
        return self.pos

    def check(self, pos):
        if isinstance(last_click, type(None)):
            return None
        if self.rect[0] <= pos[0] <= self.rect[0] + self.rect[2]:
            if self.rect[1] <= pos[1] <= self.rect[1] + self.rect[3]:
                return True
        return False


def toggle_monster_mode():
    global monster_mode
    monster_mode = not monster_mode
    resize_display()


# Input Functions

def reset_text_input():
    """Resets the current text_input to an empty string"""
    global text_input
    text_input = ""


def reset_buttons():
    """Redetermine positions of all buttons"""
    for _button in buttons:
        button_rect = None
        if _button.name == "Player Add":
            button_rect = get_player_rect(len(players), True)
        if isinstance(button_rect, type(None)):
            raise Exception("Button '" + _button.name + "' does not have a "
                                                        "position configured.")
        _button.pos = None
        _button.render(button_rect)

    for _player in players:
        _player.reset_buttons()
        _player.name_pos = None
        _player.combat_strength = None
        _player.stat_sizes = {stat: None for stat in _player.stat_sizes}


# Input Initialization
text_input = ""
last_click = None


# Display Functions
def resize_display(_size=None):
    global display, player_window_rect, old_resolution
    flags = pygame.RESIZABLE
    if fullscreen:
        flags = pygame.FULLSCREEN
        # display_info = pygame.display.Info()
        # _size = (display_info.current_w, display_info.current_h)
        if isinstance(old_resolution, type(None)):
            old_resolution = (display.get_width(), display.get_height())
        _size = true_res_compatible
    else:
        if isinstance(_size, type(None)):
            _size = display.get_width(), display.get_height()
        elif _size[0] < min_window_width:
            _size = (min_window_width, size[1])

    display = pygame.display.set_mode(_size, flags)
    display.fill(BACKGROUND_COLOR)
    pygame.display.flip()
    pygame.display.set_caption(WINDOW_CAPTION)
    w, h = display.get_width(), display.get_height()
    if monster_mode:
        w /= 2
    player_window_rect = (0, 0, w, h)
    render_players()
    reset_buttons()


def render_players():
    global last_click

    for i, player in enumerate(players):
        player.render(get_player_rect(i))
        player.check_buttons()


def render_objects():
    global last_click

    render_players()

    # Convert player rect to button rect
    for button in buttons:
        button.render()
        if button.check(last_click):
            last_click = None
            if button.name == "Player Add":
                players.append(Player(random.choice(player_names)))
                resize_display()
            else:
                raise Exception("Button '" + button.name
                                + "' does not have a function configured.")

    last_click = None


# Display Initialization
player_window_rect = None
player_names = ["Reece", "Graham", "Ryan", "Nick", "Tanner", "Josh", "Nolan"]
players = [Player(random.choice(player_names))]

buttons = [Button("Player Add", "+")]

display = None
resize_display(DEFAULT_RESOLUTION)

running = True
while running:

    for event in pygame.event.get():
        if event.type == pygame.VIDEORESIZE:
            size = event.dict["size"]
            resize_display(size)
        elif event.type == pygame.QUIT:
            running = False
            break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                break
            elif event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if not fullscreen:
                    res = old_resolution[:]
                    old_resolution = None
                else:
                    res = None
                resize_display(res)
            elif event.key == pygame.K_BACKSPACE:
                if len(text_input) > 0:
                    text_input = text_input[:-1]
            elif event.key == pygame.K_UP:
                toggle_monster_mode()
            else:
                text_input += event.dict["unicode"]

        elif event.type == pygame.MOUSEBUTTONDOWN:
            last_click = event.dict["pos"]

    if not running:
        break

    render_objects()

    window_width = player_window_rect[2]
    pygame.draw.line(display, DEFAULT_BORDER_COLOR, (window_width, 0),
                     (window_width, display.get_height()), BORDER_WIDTH)

    pygame.display.flip()
    display.fill(BACKGROUND_COLOR)

pygame.quit()
