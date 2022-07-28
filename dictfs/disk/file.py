# -*- coding: utf-8 -*-
#
#  Copyright 2022 Ramil Nugmanov <nougmanoff@protonmail.com>
#  This file is part of dictfs.
#
#  dictfs is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <https://www.gnu.org/licenses/>.
#
from pathlib import Path
from stat import S_IMODE
from typing import Union
from ..wrappers import *


class File:
    __slots__ = ('_path', '_mode')

    @property
    def mode(self):
        return self._mode

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return self._path.stat().st_size

    def __init__(self, *, path: Union[str, Path, None] = None, mode: int = 0o640):
        if path is None:  # new empty file
            self._mode = S_IMODE(mode)
            return
        elif isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError

        self._path = path
        self._mode = S_IMODE(path.stat().st_mode)

    def __repr__(self):
        return f"{type(self).__name__}('{self._path}')"

    def __call__(self, *args, **kwargs):
        return self._path.open(*args, **kwargs)

    def to_image(self) -> Image:
        return Image(self._path)


__all__ = ['File']
