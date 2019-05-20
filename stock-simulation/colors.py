import functools


END_SEQ = "\033[0m"

class Colors(object):
    BLACK = "\033[0;30;40m"
    RED = "\033[0;31;40m"
    GREEN = "\033[0;32;40m"
    YELLOW = "\033[0;33;40m"
    BLUE = "\033[0;34;40m"
    PURPLE = "\033[0;35;40m"
    CYAN = "\033[0;36;40m"


def color_text(color, text):
    return "{}{}{}".format(color, text, END_SEQ)


def generate_color_functions():
    for color_name in Colors.__dict__.keys():
        if not color_name.startswith("__"):
            color = Colors.__dict__[color_name]
            globals()[color_name.lower()] = functools.partial(color_text, color)


generate_color_functions()


if __name__ == "__main__":
    print(red("hello world"))
    print(black("hello world"))
    print(yellow("hello world"))
    print(blue("hello world"))
    print(purple("hello world"))
    print(cyan("hello world"))
