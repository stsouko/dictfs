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
from typing import Optional
from s3fs import S3FileSystem
from ..wrappers import *


class S3File:
    __slots__ = ('_path', '_s3')

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return self._s3.size(self._path)

    def __init__(self, *, path: Optional[str] = None, s3fs: Optional[S3FileSystem] = None):
        if path is None:
            return
        elif not isinstance(path, str):
            raise TypeError

        self._path = path
        self._s3 = s3fs

    def __repr__(self):
        return f"{type(self).__name__}('{self._path}')"

    def __call__(self, *args, **kwargs):
        return self._s3.open(self._path, *args, **kwargs)

    def to_image(self) -> Image:
        return Image(self._s3.open(self._path))


__all__ = ['S3File']
