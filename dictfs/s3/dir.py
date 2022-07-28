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
from os.path import basename
from typing import Optional
from s3fs import S3FileSystem
from .file import S3File


class S3Dir(MutableMapping):
    __slots__ = ('_path', '_s3', '_parent', '__dict__')

    @property
    def path(self):
        return self._path

    def __init__(self, path: Optional[str] = None, /, s3fs: Optional[S3FileSystem] = None):
        if path is None:  # empty S3 dir
            return
        elif not isinstance(path, str):
            raise TypeError

        self._s3 = S3FileSystem() if s3fs is None else s3fs

        path = path.strip('/')
        if not self._s3.isdir(path):
            raise ValueError('invalid dir')
        self._parent = None
        self._path = path

    def __repr__(self):
        return f"{type(self).__name__}('{self._path}')"

    def __iter__(self):
        return iter(self._content)

    def __len__(self):
        return len(self._content)

    def __getitem__(self, key):
        if self._content[key]:  # open subdir
            o = type(self)()
            o._parent = self
        else:
            o = S3File()
        o._s3 = self._s3
        o._path = f'{self._path}/{key}'
        return o

    def __setitem__(self, key, value):
        if key in self._content:
            raise KeyError('file/dir already exists')
        elif not key or basename(key) != key:
            raise KeyError('invalid file/dir name')

        p = f'{self._path}/{key}'
        if isinstance(value, S3Dir):
            if hasattr(value, '_path'):
                raise ValueError('empty dir object expected')
            self._virtual_dirs.add(key)
            self._content[key] = True
            value._parent = self
        elif isinstance(value, S3File):
            if hasattr(value, '_path'):
                raise ValueError('empty file object expected')
            self._s3.touch(p, truncate=False)
            self._content[key] = False
            # materialize virtual dirs up to root
            x = self
            while x._parent is not None:  # while not root
                if (k := x._path.rsplit('/', maxsplit=1)[1]) in x._parent._virtual_dirs:
                    x._parent._virtual_dirs.discard(k)
                    x = x._parent
                else:  # already materialized
                    break
        else:
            raise TypeError('dir or file expected')
        # bound dir/path
        value._path = p
        value._s3 = self._s3

    def __delitem__(self, key):
        if self._content.pop(key):  # directory
            if key in self._virtual_dirs:
                self._virtual_dirs.discard(key)
            else:
                raise OSError('Directory not empty')
        else:  # file
            self._s3.rm(f'{self._path}/{key}')
            # virtualize directories up to root
            x = self
            while x._parent is not None:
                if (k := x._path.rsplit('/', maxsplit=1)[1]) not in x._parent._virtual_dirs and \
                        len(x._virtual_dirs) == len(x._content):
                    # mark current directory as virtual
                    x._parent._virtual_dirs.add(k)
                    x = x._parent
                else:
                    break

    def refresh(self):
        self.__dict__.clear()
        self._s3.invalidate_cache()

    @cached_property
    def _virtual_dirs(self):
        return set()

    @cached_property
    def _content(self):
        s = len(self._path) + 1
        return {y: x['type'] == 'directory' for x in self._s3.ls(self._path, detail=True) if (y := x['name'][s:])}


__all__ = ['S3Dir']
