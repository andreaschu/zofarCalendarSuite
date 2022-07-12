import datetime
import tkinter


def flatten(ll):
    """
    Flattens given list of lists by one level

    :param ll: list of lists
    :return: flattened list
    """
    return [it for li in ll for it in li]


def timestamp() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')


def use_clipboard(paste_text=None):
    tk = tkinter.Tk()
    tk.withdraw()
    if type(paste_text) == str:  # Set clipboard text.
        tk.clipboard_clear()
        tk.clipboard_append(paste_text)
    try:
        clipboard_text = tk.clipboard_get()
    except tkinter.TclError:
        clipboard_text = ''
    tk.update()  # Stops a few errors (clipboard text unchanged, command line program unresponsive, window not destroyed).
    tk.destroy()
    return clipboard_text
