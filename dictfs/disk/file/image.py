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
from functools import cached_property
from inflection import underscore
from PIL.Image import open as popen
from PIL.ExifTags import TAGS, GPSTAGS
from .file import File


gps_tag = next(k for k, v in TAGS.items() if v == 'GPSInfo')
offset_tag = next(k for k, v in TAGS.items() if v == 'ExifOffset')


class Image(File):
    __slots__ = ('__dict__',)

    def __init__(self, *, path: str):
        if path is None:
            raise NotImplementedError('images are readonly')
        super().__init__(path=path)

    def __call__(self):
        return self._image

    def __dir__(self):
        return ['mode', 'path', 'size'] + list(self._meta)

    def __getattr__(self, attr):
        try:
            return self._meta[attr]
        except KeyError as e:
            raise AttributeError from e

    @cached_property
    def _image(self):
        return popen(self._path)

    @cached_property
    def _meta(self):
        exif = self._image.getexif()
        m = {underscore(TAGS[key]): val for key, val in exif.items() if key in TAGS}
        m.update((underscore(GPSTAGS[key]), value) for key, value in exif.get_ifd(gps_tag).items() if key in GPSTAGS)
        m.update((underscore(TAGS[key]), value) for key, value in exif.get_ifd(offset_tag).items() if key in TAGS)
        return m


__all__ = ['Image']
