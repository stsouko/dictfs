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
from magic import Magic
from os import listdir, mkdir, stat, chmod, remove, rmdir
from os.path import isdir, expanduser, abspath, join, basename
from stat import S_IMODE
from typing import Optional
from .file import MIME, File


class Dir(MutableMapping):
    __slots__ = ('_path', '_mode', '__dict__')

    @property
    def mode(self):
        return self._mode

    @property
    def path(self):
        return self._path

    def __init__(self, path: Optional[str] = None, /, *, mode: int = 0o750):
        if path is None:
            if not isinstance(mode, int):
                raise TypeError('invalid mode')
            self._mode = S_IMODE(mode)
            return

        path = abspath(expanduser(path))
        if not isdir(path):
            raise ValueError('invalid dir')

        self._path = path
        self._mode = S_IMODE(stat(path).st_mode)

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_magic'):  # class cached
            cls._magic = Magic(mime=True)
        return super().__new__(cls)

    def __repr__(self):
        return f"{type(self).__name__}('{self._path}')"

    def __iter__(self):
        return iter(self._content)

    def __len__(self):
        return len(self._content)

    def __getitem__(self, key):
        p = join(self._path, key)

        try:
            t = self._type[key]
        except KeyError:
            if key not in self._content_set:
                raise
            self._type[key] = t = None if isdir(p) else self._magic.from_file(p)

        if t is None:  # open subdir
            return type(self)(p)

        try:
            o = MIME[t]
        except KeyError:
            return File(path=p)
        else:
            return o(path=p)

    def __setitem__(self, key, value):
        if basename(key) != key or not key:
            raise KeyError('invalid file/dir name')
        elif key in self._content_set:
            raise KeyError('file/dir already exists')

        p = join(self._path, key)
        if isinstance(value, Dir):
            if hasattr(value, '_path'):
                raise ValueError('empty dir object expected')
            mkdir(p, mode=value.mode)
            self._type[key] = None
        elif isinstance(value, File):
            if hasattr(value, '_path'):
                raise ValueError('empty file object expected')
            open(p, 'a').close()  # touch file
            chmod(p, value.mode)  # set mode
        else:
            raise TypeError('dir or file expected')

        value._path = p  # set path
        self._content.append(key)
        self._content_set.add(key)

    def __delitem__(self, key):
        if key not in self._content_set:
            raise KeyError
        p = join(self._path, key)
        try:
            if self._type.pop(key) is None:
                rmdir(p)
            else:
                remove(p)
        except KeyError:
            if isdir(p):
                rmdir(p)
            else:
                remove(p)
        self._content.remove(key)
        self._content_set.discard(key)

    def refresh(self):
        self.__dict__.clear()

    @cached_property
    def _content(self):
        return sorted(listdir(self._path))

    @cached_property
    def _content_set(self):
        return set(self._content)

    @cached_property
    def _type(self):
        return {}


__all__ = ['Dir']
