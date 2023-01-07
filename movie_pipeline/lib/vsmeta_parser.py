import base64
from collections import ChainMap
import json
import logging
import struct
from io import BytesIO
from itertools import groupby

from ..lib.stream_reader import StreamReader

logger = logging.getLogger(__name__)


class ParserHelper:
    @staticmethod
    def read_md5(scanner: StreamReader, has_padding=False):
        if has_padding:
            scanner.read_uchar()
        md5 = scanner.read_str()
        return md5

    @staticmethod
    def read_image(scanner: StreamReader, has_padding=False):
        if has_padding:
            scanner.read_uchar()
        content = base64.b64decode(scanner.read_str())
        return content

    @staticmethod
    def skip_padding(scanner: StreamReader):
        scanner.read_uchar()  # padding
        return scanner.read_bytes()


class VsMetaParser:
    def __init__(self, filepath) -> None:
        self._filepath = filepath

    def do_parse(self, scanner: StreamReader, fields):
        parsed_data = []

        while True:
            try:
                field_key = scanner.read_uchar()
                field_name, field_extractor = fields[field_key]
                field_data = field_extractor()

                logger.debug(f'{field_name=}')
                parsed_data.append((field_name, field_data))
            except struct.error:
                break

        return parsed_data

    def parse_credits(self, credit_stream: BytesIO):
        logger.debug('Parsing credits...')
        parsed_data = []

        with credit_stream as s:
            scanner = StreamReader(s)
            fields = {
                0x0a: ('cast', scanner.read_str),
                0x12: ('director', scanner.read_str),
                0x1a: ('genre', scanner.read_str),
                0x22: ('writer', scanner.read_str)
            }

            parsed_data = self.do_parse(scanner, fields)
            parsed_data = groupby(parsed_data, key=lambda x: x[0])
            parsed_data = [{key: [p[1] for p in group]}
                           for key, group in parsed_data]

            return ChainMap(*parsed_data)

    def parse_backdrop(self, backdrop_stream: BytesIO):
        logger.debug('Parsing backdrop...')
        parsed_data = []

        with backdrop_stream as s:
            scanner = StreamReader(s)
            fields = {
                0x0a: ('image', lambda: ParserHelper.read_image(scanner)),
                0x12: ('image_md5', lambda: ParserHelper.read_md5(scanner)),
                0x18: ('timestamp', scanner.read_int)
            }

            parsed_data = self.do_parse(scanner, fields)
            parsed_data = groupby(parsed_data, key=lambda x: x[0])
            parsed_data = [{key: [p[1] for p in group]}
                           for key, group in parsed_data]

            return ChainMap(*parsed_data)

    def parse_tv_data(self, tv_data_stream: BytesIO):
        logger.debug('Parsing TV data...')
        parsed_data = []

        scanner = StreamReader(tv_data_stream)
        fields = {
            0x08: ('season', scanner.read_int),
            0x10: ('episode', scanner.read_int),
            0x18: ('year', scanner.read_int),
            0x22: ('release_date', scanner.read_str),
            0x28: ('locked', lambda: scanner.read_uchar() != 0),
            0x32: ('summary', scanner.read_str),
            0x3a: ('poster_data', lambda: ParserHelper.read_image(scanner)),
            0x42: ('poster_md5', lambda: ParserHelper.read_md5(scanner)),
            0x4a: ('metadata', lambda: json.loads(scanner.read_str())),
            0x52: ('backdrop', lambda: self.parse_backdrop(scanner.read_bytes()))
        }

        try:
            parsed_data = self.do_parse(scanner, fields)
        finally:
            tv_data_stream.close()

        return dict(parsed_data)

    @property
    def media_type(self):
        media_type = ['?', 'movie', 'serie', 'other']
        return media_type[self._version or 0]

    def parse(self):
        logger.info('Parsing "%s"...', self._filepath)
        f = open(self._filepath, 'rb')
        parsed_data = []

        try:
            scanner = StreamReader(f)
            fields = {
                0x12: ('title', scanner.read_str),
                0x1a: ('title2', scanner.read_str),
                0x22: ('tag_line', scanner.read_str),
                0x28: ('year', scanner.read_int),
                0x32: ('release_date', scanner.read_str),
                0x38: ('locked', lambda: scanner.read_uchar() != 0),
                0x42: ('summary', scanner.read_str),
                0x4a: ('metadata', lambda: json.loads(scanner.read_str())),
                0x52: ('credits', lambda: self.parse_credits(scanner.read_bytes())),
                0x5a: ('classification', scanner.read_str),
                0x60: ('rating', lambda: scanner.read_uchar() / 10),
                0x8a: ('poster_data', lambda: ParserHelper.read_image(scanner, has_padding=True)),
                0x92: ('poster_md5', lambda: ParserHelper.read_md5(scanner, has_padding=True)),
                0x9a: ('tv_data', lambda: self.parse_tv_data(ParserHelper.skip_padding(scanner))),
                0xaa: ('backdrop', lambda: self.parse_backdrop(ParserHelper.skip_padding(scanner)))
            }

            magic = scanner.read_uchar()
            if magic != 0x08:
                raise IOError('Invalid VsMeta provided')

            self._version = scanner.read_uchar()
            logger.info('version: %d', self._version)

            parsed_data = self.do_parse(scanner, fields)
        finally:
            f.close()

        return dict(parsed_data)
