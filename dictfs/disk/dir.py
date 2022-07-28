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
from collections.abc import MutableMapping
from functools import cached_property
from os import listdir
from os.path import basename
from pathlib import Path
from stat import S_IMODE
from typing import Union
from .file import File


class Dir(MutableMapping):
    __slots__ = ('_path', '_mode', '__dict__')

    @property
    def mode(self):
        return self._mode

    @property
    def path(self):
        return self._path

    def __init__(self, path: Union[str, Path, None] = None, /, *, mode: int = 0o750):
        if path is None:  # new directory
            self._mode = S_IMODE(mode)
            return
        elif isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError

        path = path.expanduser().absolute()
        if not path.is_dir():
            raise ValueError('invalid dir path')

        self._path = path
        self._mode = S_IMODE(path.stat().st_mode)

    def __repr__(self):
        return f"{type(self).__name__}('{self._path}')"

    def __iter__(self):
        return iter(self._content)

    def __len__(self):
        return len(self._content)

    def __getitem__(self, key: str):
        if self._content[key]:  # open subdir
            return type(self)(self._path / key)
        return File(path=self._path / key)

    def __setitem__(self, key, value):
        if key in self._content:
            raise KeyError('file/dir already exists')
        elif not key or basename(key) != key:
            raise KeyError('invalid file/dir name')

        p = self._path / key
        if isinstance(value, Dir):  # new directory
            if hasattr(value, '_path'):
                raise ValueError('empty dir object expected')
            p.mkdir(value.mode, exist_ok=False)
            self._content[key] = True
        elif isinstance(value, File):  # new file
            if hasattr(value, '_path'):
                raise ValueError('empty file object expected')
            p.touch(value.mode, exist_ok=False)
            self._content[key] = False
        else:
            raise TypeError('dir or file expected')
        value._path = p  # bound dir/file

    def __delitem__(self, key):
        p = self._path / key
        if self._content.pop(key):
            p.rmdir()
        else:
            p.unlink()

    def refresh(self):
        self.__dict__.clear()

    @cached_property
    def _content(self):
        p = self._path
        return {k: (p / k).is_dir() for k in sorted(listdir(p))}


__all__ = ['Dir']
