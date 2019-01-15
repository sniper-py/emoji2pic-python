import os
import sys
from PIL import Image, ImageFont, ImageDraw

from .emoji_directory import INITIAL_UNICODE, UNICODE_TO_PATH

RGB = 'RGB'
RGB_WHITE = (255, 255, 255)
RGB_BLACK = (0, 0, 0)
RGBA = 'RGBA'
RGBA_WHITE = (255, 255, 255, 1)
RGBA_BLACK = (0, 0, 0, 255)
RGBA_TRANSPARENT = (0, 0, 0, 0)
ZERO = 0
NEGATIVE = -1

DEFAULT_FONT_SIZE = 72
DEFAULT_IMAGE_WIDTH = 1080
MARGIN_LEFT = DEFAULT_FONT_SIZE * 1
MARGIN_RIGHT = DEFAULT_FONT_SIZE * 1
MARGIN_TOP = DEFAULT_FONT_SIZE * 1
MARGIN_BOTTOM = 0
LINE_SPACE = DEFAULT_FONT_SIZE * 1

EMOJI = 4
FULL_WIDTH = 3
HALF_WIDTH = 1
EMOJI_PIC_SIZE = 72


class Emoji2Pic(object):
    """将带有emoji的文本绘制到图片上，返回class 'PIL.Image.Image'。
       Text with emoji draw to the picture.return class 'PIL.Image.Image'

    :param text: 文本内容
    :param font: 字体
    :param half_font: ASCII字体
    :param emoji_folder: emoji图片和编码文件夹
    :param width: 图片宽度
    :param font_size: 文字大小
    :param color_mode: 图片底色模式
    :param font_color: 文字颜色
    :param background_color: 图片底色
    :param line_space: 行间距
    :param left: 左边距    left margins
    :param right: 右边距
    :param top: 上边距
    :param bottom: 下边距

    :return:class 'PIL.Image.Image'
    """

    def __init__(self, text, font, emoji_folder,

                 width=DEFAULT_IMAGE_WIDTH,
                 font_size=DEFAULT_FONT_SIZE,
                 color_mode=RGB,
                 font_color=RGB_BLACK,
                 background_color=RGB_WHITE,
                 line_space=LINE_SPACE,
                 left=MARGIN_LEFT,
                 right=MARGIN_RIGHT,
                 top=MARGIN_TOP,
                 bottom=MARGIN_BOTTOM,
                 half_font=None,
                 half_font_width=None,
                 emoji_offset=ZERO,
                 progress_bar=True
                 ):
        self.text = str(text)
        self.font = font
        self.emoji_folder = emoji_folder
        self.half_font = half_font if half_font is not None else font
        self.img_width = int(width)
        self.font_size = int(font_size)
        self.background_color_mode = color_mode
        self.font_color = font_color
        self.background_color = background_color
        self.line_space = int(line_space)
        self.margin_left = int(left)
        self.margin_right = int(right)
        self.margin_top = int(top)
        self.margin_bottom = int(bottom)
        self.half_font_width = int(half_font_width) if half_font_width is not None else int(self.font_size / 2)
        self.emoji_offset = int(emoji_offset)
        self.need_progress_bar = progress_bar

        self.x = ZERO
        self.y = ZERO
        self.progress_bar_count = ZERO
        self.text_length = ZERO
        self.paragraph_list = list()
        self.img_list = list()
        self.img = None
        self.paragraph = None
        self.char = None
        self.char_next = None
        self.char_index = None
        self.char_kind = None
        self.full_width_font_type = ImageFont.truetype(self.font, size=self.font_size)
        self.half_font_type = ImageFont.truetype(self.half_font, size=self.font_size)

    def split_paragraph(self):
        """
        分割段落
        Split paragraph
        """
        self.paragraph_list = self.text.replace('\n\n', '\n \n').split('\n')
        for paragraph in self.paragraph_list:
            self.text_length += len(paragraph)
        return

    def make_blank_img(self, img_width=None, img_height=None):
        """
        创建空白图片
        Make a blank picture
        """
        if img_width is None:
            img_width = self.img_width
        if img_height is None:
            img_height = self.font_size + self.line_space
        img = Image.new(mode=self.background_color_mode,
                        size=(img_width, img_height),
                        color=self.background_color)
        return img

    def stdout_progress_bar(self):
        """
        输出进度条
        Progress bar
        """
        self.progress_bar_count += 1
        display_length = 50
        percent_num = int(self.progress_bar_count / self.text_length * 100)
        percent_length = int(self.progress_bar_count / self.text_length * display_length)
        sys.stdout.write('\r')
        sys.stdout.write(
            'Drawing | [%s>%s] %s' % ('=' * percent_length,
                                      ' ' * (display_length - percent_length),
                                      str(percent_num) + '%'))
        sys.stdout.flush()
        return

    def draw_text(self):
        """
        每个字符按坐标绘制
        Each character is plotted by coordinates
        """
        for paragraph in self.paragraph_list:
            self.paragraph = paragraph
            self.img = self.make_blank_img()
            self.x = self.margin_left
            self.y = ZERO
            self.char_next = NEGATIVE
            for index in range(len(paragraph)):
                # 进度条
                if self.need_progress_bar is True:
                    self.stdout_progress_bar()
                # 绘制
                self.char_index = index
                if index >= self.char_next:
                    self.char = paragraph[index]
                    char_kind = self.classify_character()
                    if char_kind == HALF_WIDTH:  # 半角字符
                        self.draw_character(half_width=True)
                        self.x += self.half_font_width
                    elif char_kind == FULL_WIDTH:  # 全角字符
                        self.draw_character()
                        self.x += self.font_size
                    elif char_kind == EMOJI:  # emoji
                        self.draw_emoji()
                        self.x += self.font_size
                # 换行
                if self.x > self.img_width - (
                        self.margin_right + self.font_size) or index >= len(paragraph) - 1:
                    self.img_list.append(self.img)
                    self.img = self.make_blank_img()
                    self.x = self.margin_left
                    self.y = ZERO
        return

    def classify_character(self):
        """字符分类
        Character classification
        """
        if self.char in INITIAL_UNICODE:
            if u'\x2a' <= self.char <= u'\x39' and self.paragraph[
                                                   self.char_index:self.char_index + 3] not in UNICODE_TO_PATH:
                return HALF_WIDTH  # 半角字符
            return EMOJI  # emoji
        elif u'\x20' <= self.char <= u'\x7e':
            return HALF_WIDTH  # 半角字符
        else:
            return FULL_WIDTH  # 全角字符

    def draw_character(self, half_width=False):
        """
        绘制文本
        Draw character
        """
        if half_width is True:
            font_type = self.half_font_type
        else:
            font_type = self.full_width_font_type
        ImageDraw.Draw(self.img).text(xy=(self.x, self.y),
                                      text=self.char,
                                      fill=self.font_color,
                                      font=font_type)
        return

    def get_emoji_pic(self):
        """
        打开emoji图片
        emoji file name
        """
        length_list = INITIAL_UNICODE[self.char]
        emoji_unicode = None
        for length in length_list:
            emoji_unicode = self.paragraph[self.char_index:self.char_index + length]
            if emoji_unicode in UNICODE_TO_PATH:
                self.char_next = self.char_index + length
                break
            else:
                emoji_unicode = None
        if emoji_unicode is None:
            self.char_next = NEGATIVE
            return None
        emoji_file_name = UNICODE_TO_PATH.get(emoji_unicode)
        if emoji_file_name is None:
            self.char_next = NEGATIVE
            return None
        emoji_pic = Image.open(os.path.join(self.emoji_folder, emoji_file_name))

        return emoji_pic

    def draw_emoji(self):
        """
        绘制emoji
        """
        emoji_pic = self.get_emoji_pic()
        if emoji_pic is None:
            self.x -= self.font_size
            return

        # 更改尺寸
        if self.font_size != EMOJI_PIC_SIZE:
            emoji_pic = emoji_pic.resize((self.font_size, self.font_size), Image.ANTIALIAS)
        # 分离通道
        if emoji_pic.mode == 'RGBA':
            r, g, b, a = emoji_pic.split()  # 分离alpha通道  split alpha channel
        elif emoji_pic.mode == 'LA':
            l, a = emoji_pic.split()
        else:  # image.mode == 'P'
            emoji_pic = emoji_pic.convert('RGBA')
            r, g, b, a = emoji_pic.split()
        # 绘制
        self.img.paste(emoji_pic, (self.x, self.y + self.emoji_offset), mask=a)

        return

    def combine_img(self):
        """
        合并图片
        Merge picture
        """
        # 创建上边距图片
        img_top = self.make_blank_img(img_width=self.img_width, img_height=self.margin_top)
        self.img_list.insert(0, img_top)
        # 创建下边距图片  Create bottom margin picture
        img_bottom = self.make_blank_img(img_width=self.img_width, img_height=self.margin_bottom)
        self.img_list.append(img_bottom)

        background_height = ZERO
        y = ZERO
        for img in self.img_list:
            background_height += img.size[1]

        background_img = self.make_blank_img(img_width=self.img_width, img_height=background_height)

        for img in self.img_list:
            if self.background_color_mode == RGB:
                background_img.paste(img, (ZERO, y))
                y += img.size[1]
            elif self.background_color_mode == RGBA:
                r, g, b, a = img.split()  # 分离alpha通道
                background_img.paste(img, (ZERO, y), mask=a)
                y += img.size[1]

        return background_img

    def make_img(self):
        """
        Main program
        """
        self.split_paragraph()
        self.draw_text()
        return self.combine_img()
