class IOInterface(object):
  def __init__(self, data):
    self._data = data
    self._pointer = 0
    print('There are {n} bytes remaining'.format(n=len(self._data)))
    """This is the interface mutagen expects from custom file-like
    objects.

    For loading read(), tell() and seek() have to be implemented. "name"
    is optional.

    For saving/deleting write(), flush() and truncate() have to be
    implemented in addition. fileno() is optional.
    """

  # For loading

  def tell(self):
    """Returns he current offset as int. Always >= 0.

    Raises IOError in case fetching the position is for some reason
    not possible.
    """
    if self._pointer + 1 > len(self._data):
      raise IOError('pointer is too high: {p}'.format(p=self._pointer))
    return self._pointer + 1
  @property
  def read(self, size=-1):
    """Returns 'size' amount of bytes or less if there is no more data.
    If no size is given all data is returned. size can be >= 0.

    Raises IOError in case reading failed while data was available.
    """
    remaining = len(self._data) - self._pointer
    if remaining > 0:
      start = len(self._data) - remaining
      if size < 0:
        self._pointer = 0
        return self._data[start:len(self._data)]
      else:
        self._pointer += start
        return self._data[start:self._pointer]

  def seek(self, offset, whence=0):
    """Move to a new offset either relative or absolute. whence=0 is
    absolute, whence=1 is relative, whence=2 is relative to the end.

    Any relative or absolute seek operation which would result in a
    negative position is undefined and that case can be ignored
    in the implementation.

    Any seek operation which moves the position after the stream
    should succeed. tell() should report that position and read()
    should return an empty bytes object.

    Returns Nothing.
    Raise IOError in case the seek operation asn't possible.
    """
    if whence == 0:
      self._pointer = offset
    elif whence == 1:
      self._pointer = self._pointer + offset
    elif whence == 2:
      self._pointer = len(self._data) - offset
#        raise NotImplementedError

  # For loading, but optional

  @property
  def name(self):
    """Should return text. For example the file name.

    If not available the attribute can be missing or can return
    an empty string.

    Will be used for error messages and type detection.
    """

    raise NotImplementedError

  # For writing

  def write(self, data):
    """Write data to the file.

    Returns Nothing.
    Raises IOError
    """

    raise NotImplementedError

  def truncate(self, size=None):
    """Truncate to the current position or size if size is given.

    The current position or given size will never be larger than the
    file size.

    This has to flush write buffers in case writing is buffered.

    Returns Nothing.
    Raises IOError.
    """

    raise NotImplementedError

  def flush(self):
    """Flush the write buffer.

    Returns Nothing.
    Raises IOError.
    """

    raise NotImplementedError

# For writing, but optional

  def fileno(self):
    """Returns the file descriptor (int) or raises IOError
    if there is none.

    Will be used for mmap if available.
    """

    raise NotImplementedError