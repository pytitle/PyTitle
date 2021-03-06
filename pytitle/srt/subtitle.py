from typing import List, Optional, Union

from pytitle.logger import get_logger

from . import regex, exceptions
from .types import Line, PathType, Timestamp, Timing, Encodings

logger = get_logger(__name__)


class SrtSubtitle:
    """Subtitle object for .srt formatted subtitles"""

    def __init__(
        self,
        path: Optional[PathType] = None,
        lines: Optional[List[Line]] = None,
        encoding: Optional[str] = "utf-8",
    ) -> None:
        self.path = path
        self.encoding = encoding
        self.lines: Optional[List[Line]] = lines

    @classmethod
    def open(
        cls,
        path: PathType,
        encoding: Optional[str] = "utf-8",
        use_chardet: bool = False,
        fallback_encodings: Encodings = Encodings(),
        **kwargs,
    ) -> "SrtSubtitle":
        """Open subtitle file from a path

        :param path: the path to the subtitle file
        :type path: str
        :param encoding: the encoding of the subtitle file
        :type encoding: Optional[str]
        :param use_chardet: if True, use chardet to
            detect the encoding if 'utf-8' failed
        :type use_chardet: bool
        :return: the subtitle object
        :rtype: SrtSubtitle
        """
        with open(path, "r", encoding=encoding) as file:
            try:
                filestring = file.read()
            except UnicodeDecodeError:
                logger.debug(
                    f"Unable to decode file {path!r} with encoding"
                    f" {encoding!r}, trying to detect the encoding"
                )
                enc_index = kwargs.get("enc_index", 0)
                if encoding == "utf-8":
                    # don't try the utf-8 again if its default
                    enc_index += 1
                encoding, enc_index = fallback_encodings.get_encoding(enc_index)
                if encoding:
                    return cls.open(path=path, encoding=encoding, enc_index=enc_index)
                else:
                    logger.debug(f"Unable to detect encoding for file {path!r}")
                    if use_chardet:
                        logger.debug("Trying to use chardet to detect encoding")
                        # TODO: use chardet to detect encoding
                        raise NotImplementedError
                    raise exceptions.SrtEncodingDetectError(
                        f"Unable to detect encoding for {path!r}"
                    )
            lines = cls.parse(filestring)
            return cls(path=path, lines=lines, encoding=encoding)

    @classmethod
    def parse(cls, filestring: str) -> List[Line]:
        """Parse the string formatted as a .srt file

        :param filestring: the string of the subtitle file
        :type filestring: str
        :return: a list of Line objects
        :rtype: List[Line]
        """
        lines = list()
        for index, match in enumerate(
            regex.LINE.finditer(filestring),
            start=1,
        ):
            logger.debug(f"Parsing [index={index}]:")
            start, end, text = match.groups()
            timing = Timing.from_string(start, end)
            logger.debug(f"\ttimestamp: {timing}")
            text = text.strip()
            logger.debug(f"\ttext: {repr(text)}")
            line = Line(
                index=index,
                timing=timing,
                text=text,
            )
            lines.append(line)
        return lines

    def save(
        self,
        path: Optional[PathType] = None,
        encoding: str = None,
    ) -> None:
        """Save subtitle to a path

        :param path: the path to save the subtitle to
        :type path: str
        :param encoding: the encoding of the subtitle file
        :type encoding: str
        :return: None
        :rtype: None
        """
        path = path or self.path
        if path is None:
            raise exceptions.SrtSaveError("No path specified")

        with open(path, "w+", encoding=encoding or self.encoding) as file:
            file.write(self.output)

    def shift(
        self,
        shift_by: Timestamp,
        indexes: List[int] = None,
        lines: Optional[List[Line]] = None,
        backward: bool = False,
        start: bool = True,
        end: bool = True,
    ) -> None:
        """
        Shift the timing of one or multiple lines of subtitle, backward or forward

        :param shift_by: Timestamp object to shift by
        :type shift_by: Timestamp
        :param indexes: the index of a lines to shift, all lines if None
        :type indexes: List[int]
        :param lines: the lines to shift, all lines if None
        :type lines: List[Line]
        :param backward: if True, shift backward, otherwise forward
        :type backward: bool
        :return: None
        :rtype: None
        """
        if lines is None:
            if self.lines is None:
                raise ValueError("SrtSubtitle.lines is None and no lines specified")
            lines = self.lines

        if indexes is not None:
            lines = Line.get_lines(lines, indexes)

        for line in lines:
            line.timing.shift(shift_by, backward=backward, start=start, end=end)

    def shift_forward(
        self,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        milliseconds: int = 0,
        index: Union[int, List[int]] = None,
        lines: Optional[List[Line]] = None,
    ) -> None:
        """
        Shift the timing of a line by index or all
            lines of subtitle forward by hour, minutes, seconds, milliseconds
        shortcut for SrtSubtitle.shift(...)

        :param hours: the number of hours to shift
        :type hours: int
        :param minutes: the number of minutes to shift
        :type minutes: int
        :param seconds: the number of seconds to shift
        :type seconds: int
        :param milliseconds: the number of milliseconds to shift
        :type milliseconds: int
        :param index: the index of the line to shift, all lines if None
        :type index: Union[int, List[int]]
        :lines: the lines to shift, all lines if None
        :type lines: List[Line]
        :return: None
        :rtype: None
        """
        if isinstance(index, int):
            index = [index]
        if all([hours == 0, minutes == 0, seconds == 0, milliseconds == 0]):
            raise ValueError("No time specified")
        return self.shift(
            Timestamp(
                hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
            ),
            indexes=index,
            lines=lines,
        )

    def shift_backward(
        self,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        milliseconds: int = 0,
        index: Union[int, List[int]] = None,
        lines: Optional[List[Line]] = None,
    ) -> None:
        """
        Shift the timing of a line by index or all
            lines of subtitle backward by hour, minutes, seconds, milliseconds
        shortcut for SrtSubtitle.shift(...)

        :param hours: the number of hours to shift
        :type hours: int
        :param minutes: the number of minutes to shift
        :type minutes: int
        :param seconds: the number of seconds to shift
        :type seconds: int
        :param milliseconds: the number of milliseconds to shift
        :type milliseconds: int
        :param index: the index of the line to shift, all lines if None
        :type index: Union[int, List[int]]
        :lines: the lines to shift, all lines if None
        :type lines: List[Line]
        :return: None
        :rtype: None
        """
        if all([hours == 0, minutes == 0, seconds == 0, milliseconds == 0]):
            raise ValueError("No time specified")

        if isinstance(index, int):
            index = [index]
        return self.shift(
            Timestamp(
                hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
            ),
            indexes=index,
            lines=lines,
            backward=True,
        )

    def search(self, keyword: str, filters: str = None) -> Line:
        """
        Serach a keyword in text lines, duration in timings and line index
        """
        raise NotImplementedError

    def reindex(self) -> None:
        """Reindexes the subtitle lines by timing"""
        raise NotImplementedError

    def remove_italic(self):
        """Remove italic tags from subtitle"""
        raise NotImplementedError

    def fix_italic(self):
        """Fix italic tags from subtitle"""
        raise NotImplementedError

    def fix_arabic(self):
        """Fix arabic/persian characters in subtitle"""
        raise NotImplementedError

    def fix_question_mark(self):
        """Fix question marks for arabic/persian subtitles"""
        raise NotImplementedError

    def find_overlaps(self) -> List[Line]:
        """Find overlapping lines in subtitle"""
        raise NotImplementedError

    def __repr__(self) -> str:
        lines = len(self.lines) if self.lines is not None else 0
        return (
            f"SrtSubtitle(path={self.path!r}, "
            f"lines={lines}, "
            f"encoding={self.encoding!r}"
        )

    @property
    def output(self) -> str:
        if self.lines is None:
            raise ValueError("No lines to output")
        return "\n".join(line.output for line in self.lines)
