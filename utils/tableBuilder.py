from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Tuple

_box_drawings_light_horizontal = '\u2500'
_box_drawings_light_vertical = '\u2502'
_box_drawings_light_vertical_and_horizontal = '\u253C'


class TableColumnFormat(StrEnum):
    RIGHT_ALIGNED = 'r'
    CENTER_ALIGNED = 'c'
    LEFT_ALIGNED = 'l'
    SEPERATOR = '|'
    SPACER = ' '


class _Row(ABC):
    @abstractmethod
    def build(self, table_builder: TableBuilder):
        pass


class _SeperatorRow(_Row):
    def build(self, table_builder: TableBuilder):
        row_builder = []
        cur_col = 0
        for col in table_builder.columns:
            match col:
                case '|':
                    row_builder.append(_box_drawings_light_vertical_and_horizontal)
                case ' ':
                    row_builder.append(_box_drawings_light_horizontal)
                case 'r' | 'c' | 'l':
                    row_builder.append(_box_drawings_light_horizontal * table_builder.row_widths[cur_col])
                    cur_col += 1

        return ''.join(row_builder)


class _ContentRow(_Row, Tuple):
    def build(self, table_builder: TableBuilder):
        row_builder = []
        cur_col = 0
        for col in table_builder.columns:
            match col:
                case '|':
                    row_builder.append(_box_drawings_light_vertical)
                case ' ':
                    row_builder.append(' ')
                case 'r':
                    row_builder.append(self[cur_col].rjust(table_builder.row_widths[cur_col]))
                    cur_col += 1
                case 'c':
                    row_builder.append(self[cur_col].center(table_builder.row_widths[cur_col]))
                    cur_col += 1
                case 'l':
                    row_builder.append(self[cur_col].ljust(table_builder.row_widths[cur_col]))
                    cur_col += 1

        return ''.join(row_builder)


class TableBuilder:
    def __init__(self, *columns: TableColumnFormat):
        self.columns = columns
        self.width = len([c for c in columns if c in 'rcl'])
        self.rows: list[_Row] = []
        self.row_widths = [0] * self.width

    def add_row(self, *values: str):
        if len(values) > self.width:
            raise RuntimeError(f"Amount of values {len(values)} cannot be higher than column count {self.width}.")

        row = _ContentRow(values + (('',) * (self.width - len(values))))

        for i, value in enumerate(row):
            w = len(value)
            if w > self.row_widths[i]:
                self.row_widths[i] = w

        self.rows.append(row)

    def add_seperator_row(self):
        self.rows.append(_SeperatorRow())

    def build(self) -> str:
        return '\n'.join([row.build(self) for row in self.rows])

    def get_width(self) -> int:
        width = 0
        cur_col = 0
        for col in self.columns:
            match col:
                case '|' | ' ':
                    width += 1
                case 'r' | 'c' | 'l':
                    width += self.row_widths[cur_col]
                    cur_col += 1
        return width

    @classmethod
    def from_str(cls, colum_formats: str):
        return cls(*(TableColumnFormat(c) for c in colum_formats))
