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
from os.path import basename
from typing import Optional
from s3fs import S3FileSystem
from .file import MIME, S3File


class S3Dir(MutableMapping):
    __slots__ = ('_path', '_s3', '__dict__')

    @property
    def path(self):
        return self._path

    def __init__(self, path: Optional[str] = None, /, s3fs: Optional[S3FileSystem] = None):
        if path is None:  # empty S3 dir
            self._content = []
            return
        elif not isinstance(path, str):
            raise TypeError

        self._s3 = s3 = S3FileSystem() if s3fs is None else s3fs

        path = path.strip('/')
        if not s3.isdir(path):
            raise ValueError('invalid dir')
        self._path = path
        self.refresh()

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
        p = f'{self._path}/{key}'

        try:
            t = self._type[key]
        except KeyError:
            if key not in self._content_set:
                raise
            self._type[key] = t = None if self._s3.isdir(p) else self._check_mime(p)

        if t is None:  # open subdir
            if key in self._virtual_dirs:
                if self._s3.isdir(p):
                    self._virtual_dirs.discard(key)  # materialize virtual dirs
                elif self._s3.isfile(p):  # path overridden in other dir object to file
                    self._virtual_dirs.discard(key)
                    self._type[key] = t = self._check_mime(p)
                    try:
                        o = MIME[t]
                    except KeyError:
                        return S3File(path=p, s3fs=self._s3)
                    else:
                        return o(path=p, s3fs=self._s3)
                else:  # return virtual dir
                    d = type(self)()
                    d._s3 = self._s3
                    d._path = p
                    return d
            try:
                return type(self)(p, s3fs=self._s3)
            except ValueError:
                # dir virtualized
                d = type(self)()
                d._s3 = self._s3
                d._path = p
                self._virtual_dirs.add(key)
                return d

        try:
            o = MIME[t]
        except KeyError:
            return S3File(path=p, s3fs=self._s3)
        else:
            return o(path=p, s3fs=self._s3)

    def __setitem__(self, key, value):
        if basename(key) != key or not key:
            raise KeyError('invalid file/dir name')
        elif key in self._content_set:
            raise KeyError('file/dir already exists')

        p = f'{self._path}/{key}'
        if isinstance(value, S3Dir):
            if hasattr(value, '_path'):
                raise ValueError('empty dir object expected')
            # just add virtual dir
            self._virtual_dirs.add(key)
            self._type[key] = None
        elif isinstance(value, S3File):
            if hasattr(value, '_path'):
                raise ValueError('empty file object expected')
            self._s3.touch(p)
        else:
            raise TypeError('dir or file expected')
        value._path = p  # set path
        value._s3 = self._s3
        self._content.append(key)
        self._content_set.add(key)

    def __delitem__(self, key):
        if key not in self._content_set:
            raise KeyError
        p = f'{self._path}/{key}'
        # do full validation
        if self._s3.isdir(p):
            if key in self._virtual_dirs:
                self._virtual_dirs.discard(key)
            raise OSError('Directory not empty')
        elif self._s3.isfile(p):
            if key in self._virtual_dirs:  # drop overriden virtual dir
                self._virtual_dirs.discard(key)
            self._s3.rm(p)
        elif key in self._virtual_dirs:
            self._virtual_dirs.discard(key)

        self._type.pop(key, None)
        self._content.remove(key)
        self._content_set.discard(key)

    def refresh(self):
        self.__dict__.clear()
        s = len(self._path) + 1
        self._content = [y for x in self._s3.ls(self._path) if (y := x[s:])]

    def _check_mime(self, p):
        return self._magic.from_buffer(self._s3.open(p, block_size=100, cache_type='none').read(100))

    @cached_property
    def _type(self):
        return {}

    @cached_property
    def _virtual_dirs(self):
        return set()

    @cached_property
    def _content_set(self):
        return set(self._content)


__all__ = ['S3Dir']
