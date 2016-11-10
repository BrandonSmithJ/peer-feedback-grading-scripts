from pdfminer.converter import LTChar, TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, LITERAL_FONT
from pdfminer.pdftypes  import resolve1, list_value, dict_value, PDFObjRef
from pdfminer.pdffont   import PDFFontError, PDFType1Font, PDFTrueTypeFont, PDFType3Font, PDFCIDFont
from pdfminer.psparser  import literal_name
from pdfminer           import settings
from collections        import defaultdict

class CsvConverter(TextConverter):
    ''' Fuzzy extraction '''
    def __init__(self, separator=',', threshold=1.5, *args, **kwargs):
        TextConverter.__init__(self, *args, **kwargs)
        self.separator = separator
        self.threshold = threshold

    def end_page(self, i):
        lines = defaultdict(lambda: {})
        for child in self.cur_item._objs:  
            if isinstance(child, LTChar):
                (_, _, x, y) = child.bbox
                line = lines[int(-y)]
                line[x] = child._text#.encode(self.codec) 
        for y in sorted(lines.keys()):
            line = lines[y]
            self.line_creator(line)
            self.outfp.write(self.line_creator(line))
            self.outfp.write("\n")

    def line_creator(self, line):
        keys = sorted(line.keys())
        # calculate the average distange between each character on this row
        average_distance = sum([keys[i] - keys[i - 1] for i in range(1, len(keys))]) / len(keys)
        # append the first character to the result
        result = [line[keys[0]]]
        for i in range(1, len(keys)):
            # if the distance between this character and the last character is greater than the average*threshold
            if (keys[i] - keys[i - 1]) > average_distance * self.threshold:
                # append the separator into that position
                result.append(self.separator)
            # append the character
            result.append(line[keys[i]])
        printable_line = ''.join(result)
        return printable_line


class PDFResourceManagerFixed(PDFResourceManager):
    ''' Fixes recursive pdf object references '''
    def __init__(self, *args, **kwargs):
        PDFResourceManager.__init__(self, *args, **kwargs)

    def get_font(self, objid, spec):
        if objid and objid in self._cached_fonts:
            font = self._cached_fonts[objid]
        else:
            if settings.STRICT:
                if spec['Type'] is not LITERAL_FONT:
                    raise PDFFontError('Type is not /Font')
            # Create a Font object.
            if 'Subtype' in spec:
                subtype = literal_name(spec['Subtype'])
            else:
                if settings.STRICT:
                    raise PDFFontError('Font Subtype is not specified.')
                subtype = 'Type1'
            if subtype in ('Type1', 'MMType1'):
                # Type1 Font
                font = PDFType1Font(self, spec)
            elif subtype == 'TrueType':
                # TrueType Font
                font = PDFTrueTypeFont(self, spec)
            elif subtype == 'Type3':
                # Type3 Font
                font = PDFType3Font(self, spec)
            elif subtype in ('CIDFontType0', 'CIDFontType2'):
                # CID Font - Ensure recursive object references have been resolved
                if type(spec['CIDSystemInfo']) is not PDFObjRef:
                    for k in spec['CIDSystemInfo']:
                        if type(spec['CIDSystemInfo'][k]) is PDFObjRef:
                            spec['CIDSystemInfo'][k] = spec['CIDSystemInfo'][k].resolve()
                font = PDFCIDFont(self, spec)
            elif subtype == 'Type0':
                # Type0 Font
                dfonts = list_value(spec['DescendantFonts'])
                assert dfonts
                subspec = dict_value(dfonts[0]).copy()
                for k in ('Encoding', 'ToUnicode'):
                    if k in spec:
                        subspec[k] = resolve1(spec[k])
                font = self.get_font(None, subspec)
            else:
                if settings.STRICT:
                    raise PDFFontError('Invalid Font spec: %r' % spec)
                font = PDFType1Font(self, spec)
            if objid and self.caching:
                self._cached_fonts[objid] = font
        return font