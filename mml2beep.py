# -*- coding: utf-8 -*-

import json
from argparse import ArgumentParser
from typing import Union, List

# FREQ_TABLE = [[0 for scale in range(12)] for octave in range(9)]
#
#
# def gen_freq_table():
#     global FREQ_TABLE
#     # A4标准音高
#     FREQ_TABLE[4][9] = 440
#     # 十二平均律
#     for scale in range(8, -1, -1):
#         FREQ_TABLE[4][scale] = FREQ_TABLE[4][scale + 1] / 2 ** (1 / 12)
#     for scale in range(10, 12):
#         FREQ_TABLE[4][scale] = FREQ_TABLE[4][scale - 1] * 2 ** (1 / 12)
#     for octave in range(3, -1, -1):
#         for scale in range(12):
#             FREQ_TABLE[octave][scale] = FREQ_TABLE[octave + 1][scale] / 2
#     for octave in range(5, 9):
#         for scale in range(12):
#             FREQ_TABLE[octave][scale] = FREQ_TABLE[octave - 1][scale] * 2
#     for octave in range(9):
#         for scale in range(12):
#             FREQ_TABLE[octave][scale] = round(FREQ_TABLE[octave][scale])
#
#
# gen_freq_table()

# 音程 -> 音阶 -> 频率，按十二平均律算
FREQ_TABLE = [
    [16, 17, 18, 19, 21, 22, 23, 24, 26, 28, 29, 31],  # C0~B0（未使用）
    [33, 35, 37, 39, 41, 44, 46, 49, 52, 55, 58, 62],  # C1~B1
    [65, 69, 73, 78, 82, 87, 92, 98, 104, 110, 117, 123],
    [131, 139, 147, 156, 165, 175, 185, 196, 208, 220, 233, 247],
    [262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494],  # C4~B4
    [523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 932, 988],
    [1047, 1109, 1175, 1245, 1319, 1397, 1480, 1568, 1661, 1760, 1865, 1976],
    [2093, 2217, 2349, 2489, 2637, 2794, 2960, 3136, 3322, 3520, 3729, 3951],
    [4186, 4435, 4699, 4978, 5274, 5588, 5920, 6272, 6645, 7040, 7459, 7902]
]
DEFAULT_OCTAVE = 4
DEFAULT_LENGTH = 4
DEFAULT_TEMPO = 120


class MmlError(Exception):
    def __init__(self, line, col, reason):
        self.line = line
        self.col = col
        self.reason = reason

    def __str__(self):
        return f'line {self.line}, column {self.col}: {self.reason}'

    __repr__ = __str__


class Token:
    def __init__(self, line, col):
        self.line = line
        self.col = col


class Length:
    def __init__(self, length: Union[int, None]=None, has_dot=False):
        """
        :param length: 长度的倒数，如4代表4分音符。None表示默认
        :param has_dot: 附点长度，将长度延长一半，等效于length /= 1.5
        """
        self.length = length
        self.has_dot = has_dot


class Note(Token):
    def __init__(self, line, col, scale, length: Length):
        super().__init__(line, col)
        self.scale = scale
        self.length = length


class Pause(Token):
    def __init__(self, line, col, length: Length):
        super().__init__(line, col)
        self.length = length


class Joiner(Token):
    pass


class DefaultLength(Token):
    def __init__(self, line, col, length: Length):
        super().__init__(line, col)
        self.length = length


class Tempo(Token):
    def __init__(self, line, col, tempo: Union[int, None]):
        super().__init__(line, col)
        self.tempo = tempo


class Volume(Token):
    def __init__(self, line, col, volume: Union[int, None]):
        super().__init__(line, col)
        self.volume = volume


class Octave(Token):
    def __init__(self, line, col, octave: Union[int, None]):
        super().__init__(line, col)
        self.octave = octave


class ChangeOctave(Token):
    def __init__(self, line, col, delta_octave):
        super().__init__(line, col)
        self.delta_octave = delta_octave


class AbsoluteNote(Token):
    def __init__(self, line, col, note_index):
        super().__init__(line, col)
        self.note_index = note_index


class SyntaxAnalyzer:
    """语法分析器（兼词法分析器）"""

    # 字符 -> 音阶索引
    SCALE = {
        'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
    }

    def __init__(self):
        self._mml = ''
        self._index = 0
        self._line = 1
        self._col = 1

        self._res = [[]]

    def _preprocess(self):
        self._mml = self._mml.upper()
        self._index = 0
        self._line = 1
        self._col = 1
        if self._mml.startswith('MML@'):
            self._index += 4
            self._col += 4

        self._res = [[]]

    def parse(self, mml: str) -> List[List[Token]]:
        """返回音轨数组，每个音轨包含多个Token"""

        self._mml = mml
        self._preprocess()

        while self._index < len(self._mml):
            line = self._line
            col = self._col
            if self._cur_char == ',':
                # 新音轨
                self._read_char()
                self._res.append([])

            elif self._cur_char == ';':
                # 结束
                self._read_char()
                break

            elif self._cur_char in 'CDEFGAB':
                # 音符
                self._output(self._read_note())

            elif self._cur_char == 'R':
                # 休止符
                self._read_char()
                self._output(Pause(line, col, self._read_length()))

            elif self._cur_char == '&':
                # 连接
                self._read_char()
                self._output(Joiner(line, col))

            elif self._cur_char == 'L':
                # 预设音长
                self._read_char()
                self._output(DefaultLength(line, col, self._read_length()))

            elif self._cur_char == 'T':
                # 播放速度
                self._read_char()
                tempo = self._read_number()
                if tempo is not None and not 32 <= tempo <= 255:
                    raise MmlError(line, col, f'tempo = {tempo}，速度超出范围')
                self._output(Tempo(line, col, tempo))

            elif self._cur_char == 'V':
                # 音量
                self._read_char()
                volume = self._read_number()
                if volume is not None and not 0 <= volume <= 15:
                    raise MmlError(line, col, f'volume = {volume}，音量超出范围')
                self._output(Volume(line, col, volume))

            elif self._cur_char == 'O':
                # 音程
                self._read_char()
                octave = self._read_number()
                if octave is not None and not 1 <= octave <= 8:
                    raise MmlError(line, col, f'octave = {octave}，音程超出范围')
                self._output(Octave(line, col, octave))

            elif self._cur_char in '><':
                # 改变音程
                self._output(ChangeOctave(line, col, 1 if self._cur_char == '>' else -1))
                self._read_char()

            elif self._cur_char == 'N':
                # 绝对音高
                self._read_char()
                note_index = self._read_number()
                if note_index is None or not 1 <= note_index <= 96:
                    raise MmlError(line, col, f'note_index = {note_index}，绝对音高超出范围')
                self._output(AbsoluteNote(line, col, note_index))

            elif self._cur_char in ' \t\r':
                # 空白
                self._read_char()

            elif self._cur_char == '\n':
                # 新行
                self._read_char()
                self._line += 1
                self._col = 1

            else:
                # 错误字符
                raise MmlError(line, col, f'未预料到的字符"{self._cur_char}"')

        return self._res
    
    def _output(self, token):
        self._res[-1].append(token)
    
    def _read_char(self):
        res = self._mml[self._index]
        self._index += 1
        self._col += 1
        return res
    
    @property
    def _cur_char(self):
        return self._mml[self._index]

    def _read_number(self):
        """读数字，非数字则返回None"""

        if self._index >= len(self._mml) or not '0' <= self._cur_char <= '9':
            return None
        res = 0
        while self._index < len(self._mml) and '0' <= self._cur_char <= '9':
            res = res * 10 + int(self._cur_char)
            self._read_char()
        return res

    def _read_length(self):
        length = self._read_number()
        has_dot = False
        if self._index < len(self._mml) and self._cur_char == '.':
            has_dot = True
            self._read_char()
        return Length(length, has_dot)

    def _read_note(self):
        line = self._line
        col = self._col

        scale = self.SCALE[self._cur_char]
        self._read_char()
        if self._index < len(self._mml):
            if self._cur_char in '+#':
                scale += 1
                self._read_char()
            elif self._cur_char == '-':
                scale -= 1
                self._read_char()
        return Note(line, col, scale, self._read_length())


class MmlParser:
    """MML语法参考：https://mabinogi.fws.tw/ac_com_annzyral.php"""

    class _Track:
        def __init__(self, tokens):
            self.tokens = tokens
            self.index = 0
            # 音程
            self.octave = DEFAULT_OCTAVE
            # 预设音长
            self.default_length = DEFAULT_LENGTH
            # 播放速度（BPM，一分钟几拍）
            self.tempo = None
            # 下一个音符开始时间
            self.time = 0
            # 前面有一个连接符，正在连接状态
            self.is_joining = False
            self.beep_res = []

        def output(self, frequency, duration):
            self.time += duration
            if not self.is_joining:
                self.beep_res.append([frequency, duration])
                return
            if not self.beep_res:
                raise MmlError(self.tokens[self.index].line, self.tokens[self.index].col, '缺少被连接的音符')
            if self.beep_res[-1][0] == frequency:
                self.beep_res[-1][1] += duration
            else:
                self.beep_res.append([frequency, duration])
            self.is_joining = False

    def __init__(self):
        self._tracks = []

    def parse(self, mml: str) -> List[List[List[int]]]:
        """转换MML乐谱到beep谱

        返回音轨数组，每个音轨包含多个音符，每个音符为[频率(Hz), 持续时间(ms)]，频率为0代表延时
        """

        self._tracks = [self._Track(tokens) for tokens in SyntaxAnalyzer().parse(mml)]

        track = self._get_next_track_to_process()
        while track is not None:
            token = track.tokens[track.index]
            if isinstance(token, Note):
                # 音符
                octave = track.octave
                scale = token.scale
                if scale < 0:
                    scale = 11
                    octave -= 1
                elif scale >= 12:
                    scale = 0
                    octave += 1
                if not 1 <= octave <= 8:
                    raise MmlError(token.line, token.col, f'octave = {octave}，音程超出范围')
                track.output(FREQ_TABLE[octave][scale], self._get_duration(track, token.length))

            elif isinstance(token, Pause):
                # 休止符
                track.output(0, self._get_duration(track, token.length))

            elif isinstance(token, Joiner):
                # 连接
                track.is_joining = True

            elif isinstance(token, DefaultLength):
                # 预设音长
                length = token.length.length or DEFAULT_LENGTH
                if token.length.has_dot:
                    length /= 1.5
                track.default_length = length

            elif isinstance(token, Tempo):
                # 播放速度
                track.tempo = token.tempo

            elif isinstance(token, Octave):
                # 音程
                track.octave = token.octave or DEFAULT_OCTAVE

            elif isinstance(token, ChangeOctave):
                # 改变音程
                track.octave += token.delta_octave

            elif isinstance(token, AbsoluteNote):
                # 绝对音高
                note_index = token.note_index - 1
                octave = note_index // 12 + 1
                scale = note_index % 12
                track.output(FREQ_TABLE[octave][scale], self._get_duration(track, Length()))

            track.index += 1
            track = self._get_next_track_to_process()

        return [track.beep_res for track in self._tracks]

    def _get_next_track_to_process(self):
        res = None
        for track in self._tracks:
            if track.index >= len(track.tokens):
                # 这条音轨已经处理完
                continue
            if res is None or track.time <= res.time:
                # 时间小的先处理，如果时间一样先处理后面的音轨
                res = track
        return res

    def _get_duration(self, track, length: Length):
        tempo = None
        # tempo共用，后面的音轨优先
        for track_ in reversed(self._tracks):
            if track_.tempo is not None:
                tempo = track_.tempo
                break
        if tempo is None:
            tempo = DEFAULT_TEMPO

        length_ = length.length or track.default_length
        if length.has_dot:
            length_ /= 1.5

        return round(60 / tempo * 4 / length_ * 1000)


def main():
    parser = ArgumentParser(description='转换MML乐谱到beep谱')
    parser.add_argument('mml_file', help='输入的MML文件，格式为txt')
    parser.add_argument('beep_file', help='输出的beep文件路径。其中第一个数为频率(Hz)，如果为0则表示延时。'
                                          '第二个数为持续时间(ms)')
    parser.add_argument('-t', '--track', type=lambda x: int(x) - 1, default=1, help='输出第几个音轨，默认为1')
    parser.add_argument('-f', '--format', type=lambda x: x.lower(), choices=['json', 'cpp'],
                        default='json', help='输出格式，默认为json')
    args = parser.parse_args()

    with open(args.mml_file) as f:
        mml = f.read()
    res = MmlParser().parse(mml)
    with open(args.beep_file, 'w') as f:
        if args.format == 'json':
            json.dump(res[args.track], f)
        elif args.format == 'cpp':
            f.write("""#include <vector>

struct Note {
    unsigned int frequency;
    unsigned int duration;
};

std::vector<Note> notes = {
""")
            for i in range(0, len(res[args.track]), 6):
                f.write('    ')
                for note in res[args.track][i: i + 6]:
                    f.write(f'{{{note[0]}, {note[1]}}}, ')
                f.write('\n')
            f.write('};\n')


if __name__ == '__main__':
    main()
