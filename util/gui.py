import tkinter
from util.log import Loggable


class Window(Loggable, tkinter.Frame):
    """
    main application
    """

    def __init__(self, master=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_error_email = None
        self.logger.info('starting up')

        self.master = master

        menu = tkinter.Menu(self.master)
        self.master.config(menu=menu)


def startup_main_window(window_title: str) -> tuple:
    tmp_root = tkinter.Tk()
    tmp_app = Window(master=tmp_root)
    tmp_root.wm_title("zofar calendar suite - " + window_title)
    tmp_root.geometry('800x600')
    return tmp_app, tmp_root


if __name__ == '__main__':
    pass