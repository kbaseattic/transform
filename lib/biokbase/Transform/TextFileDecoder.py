#!/usr/bin/env python

import os
import codecs

def open_textdecoder(file=None, codec=None, chunkSize=1024):
    fp = open(file, 'rb')
    return TextFileDecoder(fp, codec, chunkSize)

class TextFileDecoder(object):
    def __init__(self, file=None, codec=None, chunkSize=1024):
        self._fp = file
        self._codec = codec
        
        # use chunk size of 1KB
        self._chunkSize = chunkSize
    
    def close(self):
        self._fp.close()

    def readline(self):
        startPosition = self._fp.tell()

        chunkString = str()       

        while 1:
            bytes = self._fp.read(self._chunkSize)

            if not bytes:
                return bytes

            nextChunk = codecs.decode(bytes, self._codec)

            eol = nextChunk.find("\n")

            if eol != -1:
                chunkString += nextChunk[:eol + 1]
                self._fp.seek(startPosition + len(codecs.encode(chunkString, self._codec)),0)
                return chunkString
        
            chunkString += nextChunk
                    
    def read(self, size):
        startPosition = self._fp.tell()

        byteString = self._fp.read(size)

        if byteString == None:
            return None

        charString = codecs.decode(byteString, self._codec)

        charBytes = len(codecs.encode(charString, self._codec))
        self._fp.seek(startPosition + charBytes)

        return charString

    def tell(self):
        return self._fp.tell()

    def seek(self, position, start=0):
        self._fp.seek(position, start)


    def find(self, s, startPosition=0, lastPosition=-1, firstByte=False):        
        filePosition = self._fp.tell()
        self._fp.seek(0,2)
        finalPosition = self._fp.tell()

        if lastPosition < 0 and abs(lastPosition) < finalPosition:
            lastPosition = finalPosition + lastPosition
        elif lastPosition < 0 or lastPosition > finalPosition:
            lastPosition = finalPosition

        if startPosition < 0 and abs(startPosition) < lastPosition:
            startPosition = lastPosition + startPosition
        elif startPosition < 0:
            startPosition = 0

        if startPosition > lastPosition:
            raise Exception("Start position greater than ending position!")

        stringLength = len(s)
        stringBytes = len(codecs.encode(s, self._codec))

        if stringBytes > lastPosition - startPosition:
            self._fp.seek(filePosition)
            return -1

        chunkSize = self._chunkSize        

        if stringBytes > chunkSize:
            chunkSize = stringBytes * 4

        if lastPosition - startPosition < chunkSize:
            chunkSize = lastPosition - startPosition

        offset = 0
        while 1:
            try:
                self._fp.seek(startPosition + offset)
                chunkString = codecs.decode(self._fp.read(chunkSize), self._codec)
            except IOError, e:
                self._fp.seek(filePosition)
                return -1                

            # look for the first instance of this string
            firstInstance = chunkString.find(s)

            if firstInstance > -1:                    
                # set the file position back to where it was before we began
                self._fp.seek(filePosition)
                
                offsetString = chunkString
                
                # if the string is at the end we are done, otherwise we need to get everything on the end after our string
                if s != chunkString[-stringLength:]:
                    if firstByte:
                        # calculate up to the start of the string
                        offsetString = chunkString[:firstInstance]
                    else:
                        # calculate up to the end of the string
                        offsetString = chunkString[:firstInstance + stringLength]                        
                
                # calculate the bytes to the string
                return startPosition + offset + len(codecs.encode(offsetString, self._codec))
            elif startPosition + offset + chunkSize == lastPosition:
                # we reached the end of the file and didn't find the string
                self._fp.seek(filePosition)
                return -1
            
            # need to read further ahead
            if startPosition + offset + chunkSize + chunkSize < lastPosition: 
                offset += chunkSize
            else:
                # the only part left is the end of the file
                chunkSize = lastPosition - startPosition


    def rfind(self, s, lastPosition=-1, startPosition=0, firstByte=False):
        filePosition = self._fp.tell()
        self._fp.seek(0,2)
        finalPosition = self._fp.tell()

        if lastPosition < 0 and abs(lastPosition) < finalPosition:
            lastPosition = finalPosition + lastPosition
        elif lastPosition < 0 or lastPosition > finalPosition:
            lastPosition = finalPosition

        if startPosition < 0 and abs(startPosition) < lastPosition:
            startPosition = lastPosition + startPosition
        elif startPosition < 0:
            startPosition = 0

        if startPosition > lastPosition:
            raise Exception("Start position greater than ending position!")

        stringLength = len(s)
        stringBytes = len(codecs.encode(s, self._codec))

        if stringBytes > lastPosition - startPosition:
            self._fp.seek(filePosition)
            return -1

        chunkSize = self._chunkSize * 4

        if stringBytes > chunkSize:
            chunkSize = stringBytes * 4

        if lastPosition - startPosition < chunkSize:
            chunkSize = lastPosition - startPosition

        offset = 0
        while 1:
            try:
                self._fp.seek(lastPosition - offset - chunkSize)
                chunkString = codecs.decode(self._fp.read(chunkSize), self._codec)
            except IOError, e:
                self._fp.seek(filePosition)
                return -1

            # look for the last instance of this string                
            lastInstance = chunkString.rfind(s)

            if lastInstance > -1:
                # set the file position back to where it was before we began
                self._fp.seek(filePosition)

                remainderString = chunkString

                # if the string is at the end we are done, otherwise we need to get everything on the end after our string
                if s != chunkString[-stringLength:]:
                    if firstByte:
                        # calculate up to the start of the string
                        remainderString = chunkString[:lastInstance]
                    else:
                        # calculate up to the end of the string
                        remainderString = chunkString[:lastInstance + stringLength]

                # calculate the bytes to the string
                return lastPosition - offset - chunkSize + len(codecs.encode(remainderString, self._codec))
            elif lastPosition - offset - chunkSize <= 0:
                # we reached the beginning of the file and didn't find the string
                self._fp.seek(filePosition)
                return -1

            # need to read further back
            if lastPosition - offset - chunkSize - chunkSize > 0:                
                offset += chunkSize - stringLength
            else:
                # the only part left is the beginning of the file                
                offset += chunkSize - stringLength
                chunkSize = lastPosition - offset
                   
