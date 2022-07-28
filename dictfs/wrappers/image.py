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
from inflection import underscore
from lazy_object_proxy import Proxy
from PIL.Image import open as popen
from PIL.ExifTags import TAGS, GPSTAGS


gps_tag = next(k for k, v in TAGS.items() if v == 'GPSInfo')
offset_tag = next(k for k, v in TAGS.items() if v == 'ExifOffset')


class Image(Proxy):
    __slots__ = '__meta_cache__',

    def __init__(self, file, /):
        self.__wrapped__ = popen(file)

    def __dir__(self):
        return dir(self.__wrapped__) + list(self.__meta__)

    def __getattr__(self, attr):
        try:
            return self.__meta__[attr]
        except KeyError:
            return super().__getattr__(attr)

    @property
    def __meta__(self):
        if hasattr(self, '__meta_cache__'):
            return self.__meta_cache__
        exif = self.__wrapped__.getexif()
        m = {'exif_' + underscore(TAGS[key]): val for key, val in exif.items() if key in TAGS}
        m.update(('exif_' + underscore(GPSTAGS[key]), value)
                 for key, value in exif.get_ifd(gps_tag).items() if key in GPSTAGS)
        m.update(('exif_' + underscore(TAGS[key]), value)
                 for key, value in exif.get_ifd(offset_tag).items() if key in TAGS)
        self.__meta_cache__ = m
        return m


__all__ = ['Image']
