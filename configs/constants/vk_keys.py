import win32con # type: ignore

VK_MAP = {
    # Movement
    "left":  win32con.VK_LEFT,
    "right": win32con.VK_RIGHT,
    "up":    win32con.VK_UP,
    "down":  win32con.VK_DOWN,

    # Basic keys
    "space": win32con.VK_SPACE,
    "enter": win32con.VK_RETURN,
    "esc":   win32con.VK_ESCAPE,
    "tab":   win32con.VK_TAB,

    # Modifiers
    "alt": win32con.VK_MENU,
    "altleft": win32con.VK_MENU,
    "ctrl": win32con.VK_CONTROL,
    "shift": win32con.VK_SHIFT,

    # Function keys
    "f1": win32con.VK_F1,
    "f2": win32con.VK_F2,
    "f3": win32con.VK_F3,
    "f4": win32con.VK_F4,
    "f5": win32con.VK_F5,
    "f6": win32con.VK_F6,
    "f7": win32con.VK_F7,
    "f8": win32con.VK_F8,
    "f9": win32con.VK_F9,
    "f10": win32con.VK_F10,
    "f11": win32con.VK_F11,
    "f12": win32con.VK_F12,

    # Specials
    "home":  win32con.VK_HOME,
    "end":   win32con.VK_END,
    "pageup": win32con.VK_PRIOR,
    "pagedown": win32con.VK_NEXT,
    "insert": win32con.VK_INSERT,
    "delete": win32con.VK_DELETE,
}
