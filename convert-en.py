#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import re
import os
import sys
import multiprocessing

reVerseOrder = re.compile('<verseOrder[^>]*>(.+?)</verseOrder>')
reVerseWithLines = re.compile(
    r'<verse name="([vcpbeo]\d*)[^"]*"[^>]*>((.|\n)+?)</verse>', re.M)
reMultispace = re.compile(" {2,}", re.M)
reToDelete = [re.compile('<chord[^>]+?>'),
              re.compile(r'<comment>(.|\n)+?</comment>', re.M),
              re.compile(r'</?tag[^>]*>')
              ]
reToOneNewLine = re.compile(r'(\s*</?br/?>\s*)', re.M)  # run me 2 times
reTitle = re.compile('<title>(.+?)</title>')
reGetDig = re.compile(r'(\d+)')
reNewlines = re.compile(r'(\n)+')
reWhiteSpace = re.compile(r"(\s+)")
reLines = re.compile("<lines[^>]*>(.+?)</lines>", re.M)
translateTable = {"v": "Verse", "c": "Chorus",
                  "p": "Pre Chorus", "e": "Ending", "b": "Bridge", "o": "Other"}
# translateTable = {"v": "Sloka", "c": "Refren",
#                  "p": u"Před refren", "e": "Konec", "b": "Bridge", 'o': "Jiné"}
reXML = re.compile(r'(.+?)\.xml')
reBadComas = re.compile("([A-Za-z]),([A-Za-z])", re.M)
isWin = os.name == "nt"
reContainSlash = re.compile(r"[/\\]") if isWin else re.compile("/")
eol = "\r\n" if not isWin else "\n"


class OpenLiricsDocument:
    def __init__(self, xml):
        self.title = next(reTitle.finditer(xml)).group(1).strip()
        self.verse_order = None
        try:
            self.verse_order = next(
                reVerseOrder.finditer(xml)).group(1).strip()
            self.verse_order = self.verse_order.split(" ")
            if len(self.verse_order) is 0:
                self.verse_order = None
        except StopIteration:
            pass
        self.line_structure = OpenLiricsDocument.__parse_lines(
            xml)  # type: dict
        if self.verse_order is None:
            self.line_structure = dict(
                sorted(self.line_structure.items(), key=lambda x: x[1][0]))
            self.verse_order = list()
            for key in self.line_structure:
                self.verse_order.append(key)
        i = 0
        while i < len(self.verse_order):
            if self.verse_order[i] not in self.verse_order:
                self.verse_order.pop(i)
            else:
                i += 1

    @staticmethod
    def __field_from_key(src):
        field = ""
        if len(src) > 0 and src[0] in translateTable:
            dig_match = reGetDig.search(src)
            if dig_match is not None:
                numstr = dig_match.group(1)
                numint = int(numstr)
                ender = ""

                def enderMaker(numa):
                    if(1 == numa):
                        return"st"
                    elif(2 == numa):
                        return"nd"
                    elif (3 == numa):
                        return"rd"
                    else:
                        return"th"

                if numint <= 20:
                    ender = enderMaker(numint)
                else:
                    ender = enderMaker(numint % 10)
                ender+=" "
                field += numstr + ender
            field += translateTable[src[0]]
        return field

    def escape_title_to_path(self):
        return reContainSlash.sub(r"／", self.title)

    @staticmethod
    def __parse_lines(xml):
        lines = dict()
        it = 0

        def fix_comas(str_in):
            return reBadComas.sub(r"\1, \2", str_in)

        def fix_multispace(instr):
            return reMultispace.sub(" ", instr)

        def line_maker(verse):
            strout = ""
            for one in verse:
                strout += "/n"
                strout += one.group(1).strip()
            if just_white_space(strout):
                return ""
            return strout

        for match in reVerseWithLines.finditer(xml):
            try:
                if match.group(1) not in lines:
                    itter = reLines.finditer(match.group(2))
                    loaded_itter = fix_comas(next(itter).group(1).strip())
                    loaded_itter = fix_multispace(loaded_itter)
                    pom = [it, loaded_itter if not just_white_space(
                        loaded_itter) else "", False]
                    pom[1] += line_maker(itter)
                    if not pom[1] == "":
                        lines[match.group(1)] = pom
                else:
                    lines[match.group(
                        1)][1] += line_maker(reLines.finditer(match.group(2)))
            except StopIteration:
                pass
            it += 1
        for key, value in lines.items():
            for regDel in reToDelete:
                lines[key][1] = regDel.sub("", value[1])
            lines[key][1] = reToOneNewLine.sub(r"/n", value[1])
        return lines

    def to_string(self):
        out = "[File]" + eol + "Fields="
        any_unused = False
        # resolving fields
        verseIter = iter(self.verse_order)
        out += OpenLiricsDocument.__field_from_key(next(verseIter))
        for verse in verseIter:
            out += "/t" + OpenLiricsDocument.__field_from_key(verse)
            self.line_structure[self.verse_order[0]][2] = True
        for key, value in self.line_structure.items():
            if not value[2]:
                any_unused = True
                self.line_structure = dict(
                    sorted(self.line_structure.items(), key=lambda x: x[1][0]))
                break
        if any_unused:
            for key in self.line_structure:
                if not self.line_structure[key][2]:
                    out += "/t" + OpenLiricsDocument.__field_from_key(key)
        # generating words
        out += eol + "Words="
        verses = iter(self.verse_order)
        out += self.line_structure[next(verses)][1]
        for verse in verses:
            out += "/t" + self.line_structure[verse][1]

        if any_unused:
            for key, value in self.line_structure.items():
                if not value[2]:
                    out += "/t"+self.line_structure[key][1]
        out = out.strip("\n")
        return out


def get_xmls_in_dir(dir="."):
    return [it for it in os.listdir(dir) if reXML.match(it) is not None]


def just_white_space(data):
    white_space_match = reWhiteSpace.match(data)
    if white_space_match is not None and white_space_match.group(1) == data:
        return True
    return False  # def


def convert_in_range(target_folder, start, end):
    to_convert = get_xmls_in_dir()
    i = start
    spinner = ["\\", "|", "/", "-"]
    spinnerCtr = 0
    print("     "+spinner[spinnerCtr], end="\r")
    problematicFiles = list()
    while i < end:
        try:
            print("     "+spinner[spinnerCtr], end="\r")
            infile = open(to_convert[i], encoding="utf-8")
            openliric_doc = OpenLiricsDocument(infile.read())
            infile.close()
            target_filename = target_folder + \
                openliric_doc.escape_title_to_path() + ".usr"
            if os.path.exists(target_filename):
                problematicFiles.append(
                    to_convert[i] + '    [Same title like something else]')
                i += 1
                continue
            outfile = open((target_filename), "w", encoding="utf-8")
            outfile.write(openliric_doc.to_string())
            outfile.close()
            spinnerCtr += 1
            if not spinnerCtr < len(spinner):
                spinnerCtr = 0
        except:
            problematicFiles.append(to_convert[i] + "    [Unknown problem]")
        i += 1
    if len(problematicFiles) > 0:
        print(eol+eol+"There are some problematic files that may be traslated incorectly or not at all")
        print(eol+"format is filename.xml    [problem]"+eol+eol)
        for baka in problematicFiles:
            print(baka+eol)


if __name__ == '__main__':
    filecount = len([i for i in os.listdir(".") if reXML.match(i) is not None])
    if filecount < 1:
        try:
            input("no xml files found this program will terminate")
        except KeyboardInterrupt:
            exit(0)
        import sys
        sys.exit(-1)
    print("Found %d XMLS" % filecount)
    import time

    def folder_writeable(path):

        def sleep_for_max(res, times, cond_for_end=True):
            counter = 0
            while not cond_for_end and counter <= times:
                counter += 1
                time.sleep(res)
            return not counter > times

        succes = False
        try:
            tt = open(path + "test.txt", "w")
            tt.write("test")
            tt.close()
            succes = True
        except FileNotFoundError:
            print("Canot write or read to folder")
        except PermissionError:
            print("No premision to folder")
        if succes:
            sleep_for_max(0.1, 20)
            os.remove(path + "test.txt")
        return succes

    end_w_slash = re.compile(r"[/\\]$", re.M)
    try:
        out_folder = input(
            "please select folder where we should place result of translation result(s):").strip()
        if end_w_slash.search(out_folder) is None:
            out_folder += "/"

        while not folder_writeable(out_folder):
            out_folder = input("try again:").strip()
            if end_w_slash.search(out_folder) is None:
                out_folder += "/"
            folder_not_ok = not folder_writeable(out_folder)
    except KeyboardInterrupt:
        exit(0)
    done = list()
    ctr = 0
    subproceses = list()
    start = 0
    haveProblems = False
    try:
        print("conversion started")
        convert_in_range(out_folder, 0, filecount)
        print("done")
    except KeyboardInterrupt:
        haveProblems = True
        print("interupted by user")
    except:
        import traceback
        print("something went wrong")
        traceback.print_exc(file=sys.stdout)
    finally:
        input("program will terminate")
    exit(0)


# https://support.renewedvision.com/article/163-using-group-labels-to-organize-your-slides

# https://support.renewedvision.com/article/304-how-do-i-import-plain-text-files-into-propresenter
