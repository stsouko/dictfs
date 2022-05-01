DictFS
======

Directories to Dictionaries Mapper

Example usage::

    from dictfs import Dir, File

    d = Dir('path/to/dir')  # directory2dict map object
    s = d['subdir_name']  # new d2d object
    f = d['file_name']  # file object
    print(f.mode, f.size)

    with f('w') as w:  # open file. open function arguments supported.
        w.write('hello world')

    d['new_file'] = f = File(mode=0o640)  # create new file. unix file rights supported.
    d['new dir'] = Dir(mode=0o750)  # create new subdir

    f('w').write('line')
    print(f().read())

    del d['new_file']  # remove file
    del d['new dir']  # remove empty dir

    for n, o in d.items():
        if isinstance(o, File):
            data = o().read()
            ...


File class can be instantiated and extended.

Image file class::

    from dictfs.disk.file import Image

    i = d['image.jpg']
    if isinstance(i, Image):
        print(i.gps_latitude, i.gps_longitude)  # exif info mapped to attrs
        p = i()  # PIL image object


S3 buckets mapper with same API::

    from s3fs import S3FileSystem
    from dictfs import S3Dir, S3File

    d = S3Dir('bucket/dir', s3fs=S3FileSystem(auth, params))
    d = S3Dir('bucket/dir')  # default boto3 config params

    d['subdir'] = s = S3Dir()  # create virtual dir. s3 is a plain file storage. dirs are just part of filename separated with '/'
    d['subdir']['file1'] = S3File()  # create empty file and materialize virtual dir
    s['file2']  = S3File()  # same

    f = d['subdir']['file1']
    f('w').write('hello world')

    del d['subdir']['file1']
    del d['subdir']['file2']
    del d['subdir']  # only virtual dir can be removed


ToDo
====

* SSH mapper
* Python sugar for copy and move
* Attrs modification
* More specific file classes
