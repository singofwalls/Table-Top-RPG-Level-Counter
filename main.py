# TODO: Notes button
# TODO: Highlight epic/winners
# TODO: Sounds

# TODO: Hold down on +/- for speed inc/dec
# TODO: Auto launch on screen keyboard exe if in touchscreen mode
# TODO: Monster names should count (Monster1, Monster2, etc.)
# TODO: Do not add numbers to name abbreviations


import random
import time
import ctypes
import bisect
import traceback
from ctypes import windll

from files import check_path, get_game_root

import pygame

pygame.init()

# Constants Initialization

# RESOLUTION STUFF
DEFAULT_RESOLUTION = (1400, 750)
old_resolution = DEFAULT_RESOLUTION
# Get actual resolution including zoom
ctypes.windll.user32.SetProcessDPIAware()
TRUE_RES = (windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1))
# Find closest compatible resolution
RESOLUTIONS = [
    (1024, 768),
    (1280, 800),
    (1366, 768),
    (1280, 1024),
    (1920, 1080),
]  # TODO: Scale display instead of choosing closest
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
CLICK_COLOR = (255, 255, 255)
DEFAULT_BORDER_COLOR = (52, 54, 56)
COMBAT_STRENGTH_COLOR = (214, 150, 33)
STAT_COLOR = (255, 255, 255)
LEVEL_COLOR = (102, 216, 238)
RUN_COLOR = (229, 218, 116)
BORDER_WIDTH = 3
DEFAULT_TEXT_COLOR = (255, 255, 255)
DEFAULT_FONT = "fredokaone, segoeuiblack, couriernew"

PLAYER_WIDTH = 250
BUTTON_WIDTH = 50
OPTION_BUTTON_WIDTH = BUTTON_WIDTH
MARGIN = BUTTON_WIDTH * 1.5
player_height = PLAYER_WIDTH * 1.50
player_quarter = player_height / 4
min_window_width = PLAYER_WIDTH + MARGIN * 2

WINDOW_CAPTION = "RPG Level Counter"

PLAYER_BUTTON_NAMES = ["Level", "Gear", "1Shot", "Misc", "Speed"]
MONSTER_BUTTON_NAMES = ["Level", "Gear", "1Shot", "Misc", "Speed"]
COMBAT_COMPONENTS = PLAYER_BUTTON_NAMES[:-1]

CLICK_TIME = .1

MIN_SCROLLBAR_SIZE = 30
SCROLLBAR_WIDTH = BUTTON_WIDTH

COMBAT_WINDOW_MULT = 4

font_objects = {}

SEXES = ["M", "F", "N", "B"]


# Pygame Functions


def check_in_combat():
    return len(combat_players) > 0


def get_font_object(_size, font_name=None):
    if isinstance(font_name, type(None)):
        font_name = DEFAULT_FONT
    if font_name in font_objects:
        if _size in font_objects[font_name]:
            font = font_objects[font_name][_size]
        else:
            font = pygame.font.SysFont(font_name, _size)
            font_objects[font_name][_size] = font
    else:
        font = pygame.font.SysFont(font_name, _size)
        font_objects[font_name] = {_size: font}
    return font


def display_text(text, pos, color, _size, font_name=None):
    label = get_font_object(_size, font_name).render(text, 1, color)
    display.blit(label, pos)


def get_text_dimensions(text, _size):
    return get_font_object(_size).size(text)


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


def start_keyboard():
    # TODO: Launch osk
    pass


# Player Initialization


def create_player_from_dict(player_dict):
    _player = Player(
        player_dict["name"], player_dict["monster"], player_dict["in combat"]
    )
    _player.sex_num = player_dict["sex num"]
    _player.warrior = player_dict["warrior"]
    _player.levels = player_dict["levels"]
    _player.ignored_levels = player_dict["ignored levels"]
    return _player


class Player:
    def __init__(self, name, monster=False, in_combat=False):
        self.name = name
        self.monster = monster
        self.color = DEFAULT_PLAYER_COLOR
        self.name_rect = None
        self.name_size = None
        self.warrior = False
        self.sex_num = 0

        combat_dir = ">"
        if self.monster or in_combat:
            combat_dir = "<"

        # Add player buttons
        self.buttons = [Button("Remove", "X", NEGATIVE_BUTTON_COLOR)]
        if not self.monster:
            self.buttons += [
                Button("Options Dice", "D", RUN_COLOR),
                Button("Options Warrior Toggle", "W", NEGATIVE_BUTTON_COLOR),
                Button("Options Sex Toggle", "M", RUN_COLOR),
                Button("Options Combat Add", combat_dir, RUN_COLOR),
            ]

        # Button("Options Notes", "N", RUN_COLOR),
        # TODO: Add above option and functionality

        button_names = PLAYER_BUTTON_NAMES
        if self.monster:
            button_names = MONSTER_BUTTON_NAMES  # TODO: Add speed modifier
        for button_name in button_names:
            self.buttons.append(Button(button_name + " Up", "+", POSITIVE_BUTTON_COLOR))
            self.buttons.append(
                Button(button_name + " Down", "-", NEGATIVE_BUTTON_COLOR)
            )

        self.rect = None
        self.naming = False
        self.name_pos = None

        self.ignored_levels = []
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

        self.stat_rects = {}
        self.level_rects = {}

    def create_player_dict(self):
        player_dict = {
            "name": self.name,
            "monster": self.monster,
            "in combat": self in combat_players,
            "sex num": self.sex_num,
            "warrior": self.warrior,
            "levels": self.levels,
            "ignored levels": self.ignored_levels,
        }
        return player_dict

    def determine_strength(self):
        # Only sum components to combat strength if not ignored
        self.combat_strength = sum(
            self.levels[stat]
            if stat in COMBAT_COMPONENTS and stat not in self.ignored_levels
            else 0
            for stat in self.levels
        )
        return self.combat_strength

    def render(self, player_rect):
        global dirty
        # Draw player box
        pygame.draw.rect(display, self.color, player_rect)
        pygame.draw.rect(display, DEFAULT_BORDER_COLOR, player_rect, BORDER_WIDTH)

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
            name_rect_half_width = player_rect[0] + player_rect[2] / 2
            self.name_pos = (name_rect_half_width - name_width / 2, player_rect[1])
        display_text(self.name, self.name_pos, DEFAULT_TEXT_COLOR, self.name_size)

        # Display combat strength
        if isinstance(self.combat_strength, type(None)):
            self.determine_strength()
            x = self.rect[0] - (MARGIN / 2)
            y = self.rect[1] - (MARGIN / 2)
            self.combat_strength_pos = (x, y)
            combat_strength_rect = self.combat_strength_pos + (MARGIN, MARGIN)
            self.combat_strength_size = get_text_size_to_fit(
                str(self.combat_strength), combat_strength_rect
            )
        display_text(
            str(self.combat_strength),
            self.combat_strength_pos + (MARGIN, MARGIN),
            COMBAT_STRENGTH_COLOR,
            self.combat_strength_size,
        )

        # Display each level name and buttons
        stat_num = 0
        level_rect = self.rect
        for button in self.buttons:
            pos = button.render(player=self)
            if not isinstance(pos, type(None)):
                x, y = pos
                x += BUTTON_WIDTH
                if "Down" in button.name:
                    # Render text
                    stat = PLAYER_BUTTON_NAMES[stat_num]
                    level = str(self.levels[stat])
                    stat_rect = (x, y, PLAYER_WIDTH - BUTTON_WIDTH * 3, BUTTON_WIDTH)
                    self.stat_rects[stat] = stat_rect
                    level_rect = (
                        stat_rect[0] + stat_rect[2] + BUTTON_WIDTH / 2,
                        stat_rect[1],
                        BUTTON_WIDTH,
                        BUTTON_WIDTH,
                    )
                    self.level_rects[stat] = level_rect
                    if stat == "Speed":
                        level_rect = level_rect[:2] + (
                            level_rect[2] / 1.5,
                            level_rect[3],
                        )
                    if isinstance(self.stat_sizes[stat], type(None)):
                        self.stat_sizes[stat] = get_text_size_to_fit(stat, stat_rect)
                        self.level_sizes[stat] = get_text_size_to_fit(level, level_rect)
                    size = self.stat_sizes[stat]
                    display_text(stat, stat_rect[:2], STAT_COLOR, size)
                    if stat in self.ignored_levels:
                        lx = stat_rect[0]
                        ly = stat_rect[1] + stat_rect[3] // 2
                        lw = stat_rect[2]
                        pygame.draw.line(
                            display,
                            NEGATIVE_BUTTON_COLOR,
                            (lx, ly),
                            (lx + lw, ly),
                            BORDER_WIDTH,
                        )
                    # Render level

                    display_text(
                        level, level_rect[:2], LEVEL_COLOR, self.level_sizes[stat]
                    )

                    if stat == "Speed":
                        x = level_rect[0] + level_rect[2] + 3
                        y = level_rect[1]
                        w = BUTTON_WIDTH * .5
                        h = BUTTON_WIDTH * .5
                        speed_rect = (x, y, w, h)
                        roll = str(self.calc_run_roll())
                        display_text(
                            roll,
                            speed_rect[:2],
                            RUN_COLOR,
                            get_text_size_to_fit(roll, speed_rect),
                        )

                    stat_num += 1

        # Display needed run away rolls for each player against own speed
        if self.monster:
            player_speeds = {}
            for _player in combat_players:
                if not _player.monster:
                    name = _player.name[: min(3, len(_player.name))]
                    name_num = 2
                    while name in player_speeds:
                        name = name[:2] + str(name_num)
                        name_num += 1
                    player_speeds[name] = _player.levels["Speed"]

            start_x = self.rect[0]
            y = level_rect[1] + level_rect[3]
            num_speeds = len(player_speeds)
            speed_width = self.rect[2] / (num_speeds + 1)
            speed_margin = speed_width / num_speeds
            height = player_quarter / 5
            for i, _player in enumerate(player_speeds):
                speed = player_speeds[_player] + self.levels["Speed"]
                needed_roll = 5 - speed
                size = get_text_size_to_fit(_player, [0, 0, speed_width, height])
                x = (
                    start_x + (i * (speed_width + speed_margin)) + speed_margin
                ) - speed_margin / 2
                text_width = get_text_dimensions(_player, size)[0]
                tx = x + (speed_width / 2) - (text_width / 2)
                display_text(_player, (tx, y), DEFAULT_TEXT_COLOR, size)

                color = RUN_COLOR
                for _button in combat_players[i].buttons:
                    if "Dice" in _button.name:
                        if _button.text != "D":
                            rolled_num = int(_button.text)
                            if rolled_num >= needed_roll:
                                color = POSITIVE_BUTTON_COLOR
                            else:
                                color = NEGATIVE_BUTTON_COLOR
                        break

                text = str(needed_roll)
                w = speed_width
                h = self.rect[1] + self.rect[3] - y - height - 3
                size = get_text_size_to_fit(text, (0, 0, w, h))
                text_width = get_text_dimensions(text, size)[0]
                nx = x + (speed_width / 2) - (text_width / 2)
                ny = y + height
                display_text(text, (nx, ny), color, size)

    def mark_dirty(self):
        self.name_size = None
        self.combat_strength = None

    def calc_run_roll(self):
        needed_roll = 5
        needed_roll -= self.levels["Speed"]
        return needed_roll

    def check_name(self):
        global text_input, dirty
        if self.naming:
            dirty = True
            self.name = text_input
            if "\r" in self.name:
                self.name = self.name[: self.name.index("\r")]
                reset_text_input()
                self.naming = False
            self.name_size = None

    def get_option_buttons(self):
        option_buttons = []
        for button in self.buttons:
            if "Options" in button.name:
                option_buttons.append(button)
        return option_buttons

    def check_buttons(self):
        global last_click, dirty

        for _button in self.buttons:
            _button.check_click_time()
            if not isinstance(last_click, type(None)):
                if _button.check(last_click):
                    clear_naming_players()
                    if "Up" in _button.name or "Down" in _button.name:
                        stat_name = _button.name[: _button.name.index(" ")]
                        self.stat_sizes[stat_name] = None

                    self.combat_strength = None
                    last_click = None
                    if _button.name == "Remove":
                        if self in players:
                            players.remove(self)
                        else:
                            combat_players.remove(self)
                            clean_combat()
                        resize_display(reset_bars=True)
                    elif "Combat" in _button.name:
                        if self in players:
                            _button.change_text("<")
                            # Players at top of combat list
                            last_player = 0
                            for player in combat_players:
                                if player.monster:
                                    break
                                last_player += 1
                            combat_players.insert(last_player, self)
                            players.remove(self)
                        else:
                            _button.change_text(">")
                            players.append(self)
                            combat_players.remove(self)
                            clean_combat()
                        self.mark_dirty()
                        resize_display(reset_bars=True)
                    elif "Warrior" in _button.name:
                        self.warrior = not self.warrior
                    elif "Sex" in _button.name:
                        self.sex_num = (self.sex_num + 1) % len(SEXES)
                        _button.change_text(SEXES[self.sex_num])
                    elif "Dice" in _button.name:
                        roll = random.randint(1, 6)
                        color = NEGATIVE_BUTTON_COLOR
                        if roll >= self.calc_run_roll():
                            color = POSITIVE_BUTTON_COLOR
                        _button.change_text(str(roll), color)
                    else:
                        modifier = 1
                        if "Down" in _button.name:
                            modifier = -1
                        stat = _button.name[: _button.name.index(" ")]
                        if stat in self.levels:
                            self.levels[stat] += modifier
                            if stat == "Speed":
                                # Reset dice roll button
                                for _button2 in self.buttons:
                                    if "Dice" in _button2.name:
                                        color = RUN_COLOR
                                        roll = _button2.text
                                        if roll != "D":
                                            roll = int(roll)
                                            if roll >= self.calc_run_roll():
                                                color = POSITIVE_BUTTON_COLOR
                                            else:
                                                color = NEGATIVE_BUTTON_COLOR
                                        _button2.change_text(color=color)
                                        break
                        else:
                            raise Exception(
                                "Button '"
                                + _button.name
                                + "' does not have a function "
                                "configured."
                            )
                    break

        # Check if name clicked
        if not isinstance(last_click, type(None)):
            self.naming = False
            if within_rect(self.name_rect, last_click):
                last_click = None
                clear_naming_players()
                self.naming = True
                start_keyboard()
                reset_text_input()

        # Check if skill clicked and reset points
        if not isinstance(last_click, type(None)):
            for stat in self.level_rects:
                level_rect = self.level_rects[stat]
                if not isinstance(level_rect, type(None)):
                    if within_rect(level_rect, last_click):
                        last_click = None
                        clear_naming_players()
                        self.levels[stat] = 0 if stat != "Level" else 1
                        self.stat_sizes[stat] = None
                        self.combat_strength = None
                        dirty = True
                        break

        # Check if skill name clicked and toggle ignore
        if not isinstance(last_click, type(None)):
            for stat in self.stat_rects:
                stat_rect = self.stat_rects[stat]
                if not isinstance(stat_rect, type(None)):
                    if within_rect(stat_rect, last_click) and not stat == "Speed":
                        last_click = None
                        clear_naming_players()
                        if stat in self.ignored_levels:
                            self.ignored_levels.remove(stat)
                        else:
                            self.ignored_levels.append(stat)
                        self.combat_strength = None
                        dirty = True
                        break

    def reset_buttons(self):
        opt_button_num = 0
        for _button in self.buttons:
            x, y, w, h = None, None, BUTTON_WIDTH, BUTTON_WIDTH
            option_buttons = self.get_option_buttons()
            # Determine x pos
            if _button.name == "Remove" or "Up" in _button.name:
                x = (self.rect[0] + self.rect[2]) - (BUTTON_WIDTH / 2)
            elif "Options" in _button.name:
                # Figure out x pos of option buttons at bottom of player
                opt_margin = self.rect[2] - (OPTION_BUTTON_WIDTH * len(option_buttons))
                opt_margin /= len(option_buttons)
                x = (
                    self.rect[0]
                    + ((opt_margin + OPTION_BUTTON_WIDTH) * opt_button_num)
                    + opt_margin / 2
                )
                opt_button_num += 1
                w, h = OPTION_BUTTON_WIDTH, OPTION_BUTTON_WIDTH
            else:
                x = self.rect[0] - (BUTTON_WIDTH / 2)

            # Determine y pos
            if _button.name == "Remove":
                y = self.rect[1] - BUTTON_WIDTH / 2
            elif "Options" in _button.name:
                y = self.rect[1] + self.rect[3] - BUTTON_WIDTH / 2
            else:
                y_level = PLAYER_BUTTON_NAMES.index(
                    _button.name[: _button.name.index(" ")]
                )
                button_area = player_height - player_quarter - BUTTON_WIDTH
                total_button_height = BUTTON_WIDTH * len(PLAYER_BUTTON_NAMES)
                button_margin = (button_area - total_button_height) / len(
                    PLAYER_BUTTON_NAMES
                )
                y = y_level * (BUTTON_WIDTH + button_margin)
                y += self.rect[1] + player_quarter
            button_rect = (x, y, w, h)
            if isinstance(button_rect[0], type(None)):
                raise Exception(
                    "Player button '"
                    + _button.name
                    + "' does not have a position configured."
                )
            _button.pos = None
            _button.render(button_rect, self)


def within_rect(rect, pos):
    if rect[0] <= pos[0] <= rect[0] + rect[2]:
        if rect[1] <= pos[1] <= rect[1] + rect[3]:
            return True
    return False


def clean_combat():
    global combat_players
    for player in combat_players:
        if not player.monster:
            break
    else:
        combat_players = []


def clear_combat():
    while len(combat_players) > 0:
        player = combat_players[0]
        if not player.monster:

            # Change combat button
            for button in player.buttons:
                if button.name == "Options Combat Add":
                    button.change_text(">")
                    break

            player.levels["1Shot"] = 0
            player.ignored_levels = []

            # Swap player list
            players.append(player)
            player.mark_dirty()
        combat_players.remove(player)
    clean_combat()
    resize_display(reset_bars=True)


def clear_naming_players():
    for player in players:
        player.naming = False
    for player in combat_players:
        player.naming = False


def get_players_per_line(window_rect, num_players, button):
    players_per_line = num_players

    if button:
        # Button fills space of player
        players_per_line += 1
    while True:
        line_players_width = players_per_line * PLAYER_WIDTH
        line_margins_width = (MARGIN * players_per_line) + MARGIN

        if line_players_width + line_margins_width > window_rect[2]:
            players_per_line -= 1
        else:
            break

    return players_per_line


def get_player_rect(player_num, player_list, button=False):
    # Try to fit all players on a line to start

    num_monsters = len(list(filter(lambda x: x.monster, player_list)))
    num_players = len(player_list) - num_monsters

    combat = False
    if player_list == players:
        window_rect = player_window_rect
    elif player_list == combat_players:
        combat = True
        window_rect = combat_window_rect

    players_per_line = get_players_per_line(window_rect, num_players, button)
    monsters_per_line = get_players_per_line(window_rect, num_monsters, button)

    is_monster = False
    if not button:
        player = player_list[player_num]
        is_monster = player.monster

    divider = 0

    x, y, my, mx = 0, 0, 0, 0
    if num_players > 0 and players_per_line > 0:
        y, x = divmod(player_num, players_per_line)
        if is_monster or (button and num_monsters > 0):
            y, x = divmod(num_players - 1, players_per_line)
            y += 1
            x = 0
            my, mx = divmod(player_num - num_players, monsters_per_line)
            divider = MARGIN

    x += mx
    x *= PLAYER_WIDTH + MARGIN
    x += MARGIN
    x += window_rect[0]
    y += my
    y *= player_height + MARGIN
    y += MARGIN
    y += window_rect[1]
    y += divider
    if combat:
        y += MARGIN

    if button:
        _button_rect = list(i for i in range(0, 4))
        _button_rect[0] = x + ((PLAYER_WIDTH / 2) - (BUTTON_WIDTH / 2))
        _button_rect[1] = (y + player_height / 2) - (BUTTON_WIDTH / 2)
        _button_rect[2], _button_rect[3] = BUTTON_WIDTH, BUTTON_WIDTH
        return _button_rect

    return (x, y, PLAYER_WIDTH, player_height), divider > 0


class Button:
    def __init__(
        self,
        name,
        text,
        text_color=POSITIVE_BUTTON_COLOR,
        color=DEFAULT_PLAYER_COLOR,
        font=None,
    ):
        self.name = name
        self.text = text
        self.text_color = text_color
        self.color = color
        self.font = font

        self.text_size = None
        self.rect = None

        self.click_time = None

        self.pos = None

    def check_click_time(self):
        global dirty, button_clicked
        if not isinstance(self.click_time, type(None)):
            if self.click_time + CLICK_TIME > time.time():
                # Show clicked
                self.color = CLICK_COLOR
                dirty = True
            else:
                self.color = DEFAULT_PLAYER_COLOR
                self.click_time = None
                button_clicked = False
                dirty = True

    def render(self, rect=None, player=None):
        if isinstance(rect, type(None)):
            if not isinstance(self.rect, type(None)):
                rect = self.rect
            else:
                return None  # If player has not yet been rendered, skip
        else:
            self.rect = rect

        self.check_click_time()

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

        # Do not render combat button when not in combat
        if not (self.name in combat_buttons and not check_in_combat()):
            if "Warrior" in self.name:
                if player.warrior:
                    self.text_color = POSITIVE_BUTTON_COLOR
                else:
                    self.text_color = NEGATIVE_BUTTON_COLOR
            pygame.draw.rect(display, self.color, rect)
            pygame.draw.rect(display, DEFAULT_BORDER_COLOR, rect, BORDER_WIDTH)
            display_text(
                self.text, self.pos, self.text_color, self.text_size, self.font
            )
        return self.pos

    def change_text(self, text=None, color=None):
        if not isinstance(text, type(None)):
            self.text = text
        self.text_size = None
        if not isinstance(color, type(None)):
            self.text_color = color
        self.render()

    def check(self, pos):
        global dirty, button_clicked
        if isinstance(last_click, type(None)):
            return None
        if self.name in combat_buttons and not check_in_combat():
            return False  # Do not click combat buttons when not in combat
        if within_rect(self.rect, pos):
            dirty = True
            self.click_time = time.time()
            button_clicked = True
            return True
        return False


# Input Functions


def reset_text_input():
    """Resets the current text_input to an empty string"""
    global text_input
    text_input = ""


def reset_drag_bars():
    player_bar.reset()
    combat_bar.reset()


def reset_buttons():
    """Redetermine positions of all buttons"""
    for _button in buttons:
        button_rect = None
        if _button.name == "Player Add":
            button_rect = get_player_rect(len(players), players, True)
        elif _button.name == "Combat Add":
            button_rect = get_player_rect(len(combat_players), combat_players, True)
        elif _button.name == "Combat End":
            button_rect = (
                display.get_width() - (BUTTON_WIDTH + MARGIN // 2) - MARGIN,
                (MARGIN - BUTTON_WIDTH) // 2,
                BUTTON_WIDTH,
                BUTTON_WIDTH,
            )
        if isinstance(button_rect, type(None)):
            raise Exception(
                "Button '" + _button.name + "' does not have a " "position configured."
            )
        _button.pos = None
        _button.render(button_rect)

    for _player in players:
        _player.reset_buttons()
        _player.name_pos = None
        _player.combat_strength = None
        _player.stat_sizes = {stat: None for stat in _player.stat_sizes}
    for _player in combat_players:  # TODO: Clean up
        _player.reset_buttons()
        _player.name_pos = None
        _player.combat_strength = None
        _player.stat_sizes = {stat: None for stat in _player.stat_sizes}


# Input Initialization
text_input = ""
last_click = None


# Display Functions
def resize_display(_size=None, force=False, reset_bars=False):
    global display, player_window_rect, old_resolution, dirty, combat_window_rect
    if not isinstance(_size, type(None)) or reset_bars:
        reset_drag_bars()
    dirty = True
    flags = pygame.RESIZABLE
    if (not isinstance(_size, type(None))) or force:
        resize = _size
    if fullscreen:
        flags = pygame.FULLSCREEN
        if isinstance(old_resolution, type(None)):
            old_resolution = (display.get_width(), display.get_height())
        resize = true_res_compatible
    else:
        if not isinstance(_size, type(None)):
            if _size[0] / COMBAT_WINDOW_MULT < min_window_width:
                resize = (int(min_window_width * COMBAT_WINDOW_MULT), resize[1])

    if (not isinstance(_size, type(None))) or force:
        display = pygame.display.set_mode(resize, flags)
    display.fill(BACKGROUND_COLOR)
    pygame.display.set_caption(WINDOW_CAPTION)
    w, h = display.get_width(), display.get_height()
    y = player_bar.get_offset()
    cy = combat_bar.get_offset()

    if check_in_combat():
        w /= COMBAT_WINDOW_MULT
    player_window_rect = (0, y, w, h)
    combat_window_rect = (w, cy, display.get_width() - w, h)
    render_players()
    reset_buttons()


def render_player_list(player_list):
    if len(player_list) < 1:
        return 0, 0
    player_start = 0
    player_rect = None
    drew_divider = False
    for i, player in enumerate(player_list):
        player_rect, monster = get_player_rect(i, player_list)
        if monster and not drew_divider:
            drew_divider = True
            x = combat_window_rect[0]
            y = player_rect[1] - MARGIN
            x2 = display.get_width()
            pygame.draw.line(
                display, DEFAULT_BORDER_COLOR, (x, y), (x2, y), BORDER_WIDTH
            )
        player.render(player_rect)
        if i == 0:
            player_start = player_rect[1]
    return player_rect[1] + player_rect[3], player_start


def render_players():
    _player_height, player_start = render_player_list(players)
    _combat_height, combat_start = render_player_list(combat_players)
    return (_player_height, player_start), (_combat_height, combat_start)


def check_naming():
    for player in players:
        player.check_name()
    for player in combat_players:
        player.check_name()


def check_buttons():
    global last_click

    for button in buttons:
        button.check_click_time()
        if not isinstance(last_click, type(None)):
            if button.check(last_click):
                last_click = None
                if button.name == "Player Add":
                    players.append(Player(random.choice(player_names)))
                    resize_display()
                elif button.name == "Combat Add":
                    combat_players.append(Player(random.choice(monster_names), True))
                    resize_display()
                elif button.name == "Combat End":
                    clear_combat()
                else:
                    raise Exception(
                        "Button '"
                        + button.name
                        + "' does not have a function configured."
                    )
    for player in players:
        player.check_buttons()
    for player in combat_players:
        player.check_buttons()


def render_combat_bar():
    if check_in_combat():
        x = combat_window_rect[0]
        w = display.get_width() - x
        h = MARGIN - BORDER_WIDTH
        pygame.draw.rect(display, DEFAULT_PLAYER_COLOR, (x, 0, w, MARGIN))
        pygame.draw.rect(display, DEFAULT_BORDER_COLOR, (x, 0, w, MARGIN), BORDER_WIDTH)

        # Total scores
        total_player_score = 0
        total_monster_score = 0
        for player in combat_players:
            if player.monster:
                total_monster_score += player.determine_strength()
            else:
                total_player_score += player.determine_strength()

        # Draw player score
        x = combat_window_rect[0] + MARGIN / 2

        text_size = get_text_size_to_fit(str(total_player_score), (x, 0, w, h))
        text = str(total_player_score)
        display_text(text, (x, 0), POSITIVE_BUTTON_COLOR, text_size)
        text_width = get_text_dimensions(text + " ", text_size)[0]
        x += text_width

        # Draw VS
        text = " Vs. "
        text_size = get_text_size_to_fit(text, (x, 0, w, h))
        display_text(text, (x, 0), DEFAULT_TEXT_COLOR, text_size)
        text_width = get_text_dimensions(text + " ", text_size)[0]
        x += text_width

        # Draw monster score
        text = str(total_monster_score)
        text_size = get_text_size_to_fit(text, (x, 0, w, h))
        display_text(str(total_monster_score), (x, 0), NEGATIVE_BUTTON_COLOR, text_size)
        text_width = get_text_dimensions(text + "  ", text_size)[0]
        x += text_width

        warrior = False
        for player in combat_players:
            if player.warrior:
                warrior = True
                total_player_score += 1
                break

        status_color = POSITIVE_BUTTON_COLOR
        status_text = "WINNING! ("
        winning = True
        if total_monster_score >= total_player_score:
            winning = False
            status_color = NEGATIVE_BUTTON_COLOR
            status_text = "LOSING! ("
        total = total_player_score - total_monster_score
        if not winning:
            total -= 1
        status_text += str(total)
        status_text += ")"
        status_pos = (x, 0)

        status_size = get_text_size_to_fit(status_text, (x, 0, w, h))
        display_text(status_text, status_pos, status_color, status_size)
        for button in buttons:
            if button.name == "Combat End":
                button.render()
                break


def render_objects():
    global last_click

    (_player_height, _player_start), (_combat_height, combat_start) = render_players()

    # Convert player rect to button rect
    player_button_height = None
    combat_button_height = None
    for button in buttons:
        if button.name == "Combat End":
            continue  # Rendered with combat bar
        pos = button.render()
        if button.name == "Player Add":
            player_button_height = pos[1] + BUTTON_WIDTH
        elif button.name == "Combat Add":
            combat_button_height = pos[1] + BUTTON_WIDTH

    player_bar_height = (
        max(_player_height, player_button_height) - _player_start + MARGIN * 2
    )
    combat_bar_height = (
        max(_combat_height, combat_button_height) - combat_start + MARGIN * 3
    )

    render_combat_bar()

    # Display combat options
    return player_bar_height, combat_bar_height


class ScrollBar:
    def __init__(self, name):
        self.name = name
        self.scrolled = 0
        self.previous_click = None
        self.bar_rect = None
        self.last_scrolled = None
        self.last_height = None
        self.h = 1
        self.total_height = 1

    def get_offset(self):
        scroll_height = display.get_height() - self.h
        if scroll_height == 0:
            return 0
        percent_scrolled = self.scrolled / scroll_height
        to_scroll = self.total_height - display.get_height()
        return -percent_scrolled * to_scroll

    def get_bar_rect(self, _height, window_rect):
        self.total_height = _height
        percent_shown = display.get_height() / self.total_height
        if percent_shown > 1:
            # All on screen
            return None

        x = window_rect[0] + window_rect[2] - SCROLLBAR_WIDTH
        y = self.scrolled
        w = SCROLLBAR_WIDTH
        self.h = max(percent_shown * display.get_height(), MIN_SCROLLBAR_SIZE)
        bar_rect = (x, y, w, self.h)
        return bar_rect

    def render(self, _height, window_rect):
        self.bar_rect = self.get_bar_rect(_height, window_rect)
        # Height now constant with scroll, must redo bar height
        if not isinstance(self.bar_rect, type(None)):
            self.last_height = _height
            pygame.draw.rect(display, DEFAULT_BORDER_COLOR, self.bar_rect)

    def on_bar(self, pos):
        if not isinstance(self.bar_rect, type(None)):
            if self.bar_rect[0] <= pos[0] <= self.bar_rect[0] + self.bar_rect[2]:
                if self.bar_rect[1] <= pos[1] <= self.bar_rect[1] + self.bar_rect[3]:
                    return True
        return False

    def check_click(self):
        """Check if mouse clicked on scroll bar"""
        global last_click
        if not isinstance(last_click, type(None)):
            if self.on_bar(last_click):
                self.previous_click = last_click
                self.last_scrolled = self.scrolled
                last_click = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            pos = event.dict["pos"]
            if not isinstance(self.previous_click, type(None)):
                self.drag_bar(self.previous_click, pos)
        if event.type == pygame.MOUSEBUTTONUP:
            # if not isinstance(self.previous_click, type(None)):
            #     resize_display()
            self.previous_click = None

    def drag_bar(self, prev, new):
        global dirty
        distance = new[1] - prev[1]
        if not isinstance(self.last_scrolled, type(None)):
            add = self.last_scrolled
        else:
            add = 0
        self.scrolled = distance + add
        dirty = True

        # Scroll back if too far
        if self.h + self.scrolled > display.get_height():
            self.scrolled = display.get_height() - self.h
        if self.scrolled < 0:
            self.scrolled = 0
        resize_display()

    def reset(self):
        self.scrolled = 0
        self.previous_click = None
        self.bar_rect = None
        self.last_scrolled = None
        self.last_height = None
        self.h = 1
        self.total_height = 1


def new_game():
    global players, combat_players
    players = [Player(random.choice(player_names))]
    combat_players = []


def main_loop():
    global dirty, running, fullscreen, old_resolution, text_input, last_click, player_window_rect, combat_window_rect, display
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
                    resize_display(res, True)
                elif event.key == pygame.K_BACKSPACE:
                    if len(text_input) > 0:
                        text_input = text_input[:-1]
                else:
                    text_input += event.dict["unicode"]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                last_click = event.dict["pos"]
            else:
                player_bar.handle_event(event)
                combat_bar.handle_event(event)

        if not running:
            break

        player_bar.check_click()
        combat_bar.check_click()
        if button_clicked or not isinstance(last_click, type(None)):
            check_buttons()
        check_naming()

        if dirty:
            display.fill(BACKGROUND_COLOR)
            player_window_height, combat_height = render_objects()
            player_bar.render(player_window_height, player_window_rect)
            if check_in_combat():
                combat_bar.render(combat_height, combat_window_rect)

            window_width = player_window_rect[2]
            pygame.draw.line(
                display,
                DEFAULT_BORDER_COLOR,
                (window_width, 0),
                (window_width, display.get_height()),
                BORDER_WIDTH,
            )

            pygame.display.flip()
            dirty = False
            save_game()


def save_game():
    last_game = [[], []]
    for player in players:
        last_game[0].append(player.create_player_dict())
    for player in combat_players:
        last_game[1].append(player.create_player_dict())

    last_game_file = open(check_path(get_game_root() + "last_game.mlcs"), "w")
    last_game_file.write(last_game.__repr__())
    last_game_file.close()


def quit_game():
    pygame.quit()
    save_game()


# Display Initialization
dirty = True

player_window_rect = None
combat_window_rect = None
player_names = ["Reece", "Graham", "Ryan", "Nick", "Tanner", "Josh", "Alec", "Erin"]
monster_names = ["Monster"]

# Load game
file_path = get_game_root() + "last_game.mlcs"
file = check_path(file_path)
last_game_file = open(file, "r")
last_game = last_game_file.read()
last_game_file.close()

button_clicked = False

players = []
combat_players = []
if len(last_game) > 0:
    try:
        last_game = eval(last_game)
        for player in last_game[0]:
            players.append(create_player_from_dict(player))
        for player in last_game[1]:
            combat_players.append(create_player_from_dict(player))
    except:
        new_game()
else:
    new_game()

combat_buttons = ["Combat Add", "Combat End"]
buttons = [
    Button("Player Add", "+"),
    Button("Combat Add", "+"),
    Button("Combat End", "End"),
]

display = None
player_bar = ScrollBar("player")
combat_bar = ScrollBar("combat")
resize_display(DEFAULT_RESOLUTION)

running = True
try:
    main_loop()
except Exception as e:
    traceback.print_exc()
finally:
    quit_game()
