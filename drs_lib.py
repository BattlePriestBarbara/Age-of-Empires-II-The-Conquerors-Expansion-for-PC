"""
Generic AoE2 DRS reader/writer (layout verified against the game's gamedata*.drs):

  0   40  copyright (NUL padded)
  40   4  version     ("1.00")
  44  12  ftype       ("tribe", NUL padded)
  56   4  int32 n_tables
  60   4  int32 offset of the first file's data
  64     n_tables x (4 ext, 4 table-info offset (absolute), 4 n_files)
  ...    per table: n_files x (4 id, 4 data offset (absolute), 4 size)
  ...    raw file data
"""
import hashlib
import struct


class Drs(object):
    def __init__(self, path):
        self.path = path
        self.data = open(path, "rb").read()
        d = self.data
        self.copyright = d[0:40]
        self.version = d[40:44]
        self.ftype = d[44:56]
        self.n_tables, self.first_off = struct.unpack_from("<ii", d, 56)
        self.tables = []            # list of (ext:bytes, [(id, off, size), ...])
        for t in range(self.n_tables):
            pos = 64 + 12 * t
            ext = d[pos:pos + 4]
            info_off, n = struct.unpack_from("<ii", d, pos + 4)
            entries = []
            for i in range(n):
                eid, off, size = struct.unpack_from("<iii", d, info_off + 12 * i)
                entries.append([eid, off, size])
            self.tables.append((ext, entries))

    def payload(self, ext, fid):
        for e, entries in self.tables:
            if e == ext:
                for eid, off, size in entries:
                    if eid == fid:
                        return self.data[off:off + size]
        raise KeyError((ext, fid))

    def digest(self, ext, fid):
        return hashlib.md5(self.payload(ext, fid)).hexdigest()

    def entries(self):
        """yield (ext, id, size, md5) for every file in the archive"""
        for ext, rows in self.tables:
            for eid, off, size in rows:
                yield ext, eid, size, hashlib.md5(self.data[off:off + size]).hexdigest()

    def build(self, replacements):
        """Return new archive bytes with {(ext, id): new_payload} applied."""
        todo = dict(replacements)
        n_tables = len(self.tables)
        head = bytearray()
        head += self.copyright
        head += self.version
        head += self.ftype
        head += struct.pack("<i", n_tables)
        head += b"\x00\x00\x00\x00"                   # first data offset (patched below)
        # table list + info blocks
        table_list_size = 12 * n_tables
        info_size = sum(12 * len(rows) for _ext, rows in self.tables)
        cur = 64 + table_list_size + info_size
        table_list = bytearray()
        info = bytearray()
        payloads = []
        for ext, rows in self.tables:
            table_list += ext
            table_list += struct.pack("<i", 64 + table_list_size + len(info))
            table_list += struct.pack("<i", len(rows))
            for eid, off, size in rows:
                data = self.data[off:off + size]
                if (ext, eid) in todo:
                    data = todo.pop((ext, eid))
                info += struct.pack("<iii", eid, cur, len(data))
                payloads.append(data)
                cur += len(data)
        if todo:
            raise KeyError("replacement target not found: %r" % sorted(todo))
        first_data_offset = cur - sum(len(p) for p in payloads) if payloads else 0
        out = bytearray()
        out += head
        out[60:64] = struct.pack("<i", first_data_offset)
        out += table_list
        out += info
        for p in payloads:
            out += p
        return bytes(out)


def repack(src, dst, replacements):
    a = Drs(src)
    before = sorted(a.entries())
    new_bytes = a.build(replacements)
    open(dst, "wb").write(new_bytes)
    b = Drs(dst)
    after = sorted(b.entries())
    changed = [(x, y) for x, y in zip(before, after) if x != y]
    same_count = sum(1 for x, y in zip(before, after) if x == y)
    return {"src": src, "dst": dst, "n_entries": len(before),
            "unchanged": same_count, "changed": changed,
            "size_before": len(a.data), "size_after": len(new_bytes)}
