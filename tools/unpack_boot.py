#!/usr/bin/env python3
"""Unpack Android boot/recovery images (header v0-v4) without platform tools.

Only needs the Python standard library for gzip/xz/bzip2 ramdisks; lz4/lzstd
are used through their command line tools when available.
"""

import argparse
import bz2
import gzip
import hashlib
import lzma
import os
import shutil
import struct
import subprocess
import sys

MAGIC = b"ANDROID!"
CPIO_NEWC = (b"070701", b"070702")


def align(value, page):
    return (value + page - 1) // page * page


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def cstr(raw):
    return raw.split(b"\x00", 1)[0].decode("utf-8", "replace")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def parse_header(data):
    if len(data) < 44 or data[:8] != MAGIC:
        raise SystemExit("error: not an Android boot image (ANDROID! magic missing)")

    version = u32(data, 40)
    info = {
        "header_version": version,
        "os_version": u32(data, 44),
    }

    if version in (0, 1, 2):
        info.update(
            kernel_size=u32(data, 8),
            kernel_addr=u32(data, 12),
            ramdisk_size=u32(data, 16),
            ramdisk_addr=u32(data, 20),
            second_size=u32(data, 24),
            second_addr=u32(data, 28),
            tags_addr=u32(data, 32),
            page_size=u32(data, 36),
            name=cstr(data[48:64]),
            cmdline=cstr(data[64:576]),
            extra_cmdline=cstr(data[608:1632]),
            recovery_dtbo_size=u32(data, 1632) if version >= 1 else 0,
            recovery_dtbo_offset=u64(data, 1636) if version >= 1 else 0,
            dtb_size=u32(data, 1648) if version >= 2 else 0,
            dtb_addr=u64(data, 1652) if version >= 2 else 0,
        )
    elif version in (3, 4):
        info.update(
            kernel_size=u32(data, 8),
            ramdisk_size=u32(data, 12),
            page_size=4096,
            cmdline=cstr(data[44:44 + 1536]),
            name="",
            extra_cmdline="",
            kernel_addr=0,
            ramdisk_addr=0,
            second_size=0,
            second_addr=0,
            tags_addr=0,
            recovery_dtbo_size=0,
            recovery_dtbo_offset=0,
            dtb_size=0,
            dtb_addr=0,
        )
    else:
        raise SystemExit(f"error: unsupported boot header version {version}")

    page = info["page_size"]
    if page <= 0 or page & (page - 1):
        raise SystemExit(f"error: invalid page size {page}")

    info["kernel_offset"] = page
    info["ramdisk_offset"] = info["kernel_offset"] + align(info["kernel_size"], page)
    info["second_offset"] = info["ramdisk_offset"] + align(info["ramdisk_size"], page)
    info["recovery_dtbo_offset_calc"] = info["second_offset"] + align(info["second_size"], page)
    info["dtb_offset"] = info["recovery_dtbo_offset_calc"] + align(info["recovery_dtbo_size"], page)

    return info


def decompress_ramdisk(raw, out_path):
    if raw[:2] == b"\x1f\x8b":
        kind = "gzip"
        data = gzip.decompress(raw)
    elif raw[:6] == b"\xfd7zXZ\x00":
        kind = "xz"
        data = lzma.decompress(raw)
    elif raw[:3] == b"BZh":
        kind = "bzip2"
        data = bz2.decompress(raw)
    elif raw[:4] in (b"\x04\x22\x4d\x18", b"\x02\x21\x4c\x18"):
        kind = "lz4"
        data = run_filter(["lz4", "-d", "-c"], raw, out_path)
    elif raw[:4] == b"\x28\xb5\x2f\xfd":
        kind = "zstd"
        data = run_filter(["zstd", "-d", "-c"], raw, out_path)
    elif raw[:6] in CPIO_NEWC:
        kind = "cpio"
        data = raw
    else:
        kind = "unknown"
        with open(out_path, "wb") as fh:
            fh.write(raw)
        return kind, len(raw)

    with open(out_path, "wb") as fh:
        fh.write(data)
    return kind, len(data)


def run_filter(argv, raw, out_path):
    exe = shutil.which(argv[0])
    if not exe:
        with open(out_path, "wb") as fh:
            fh.write(raw)
        return raw
    proc = subprocess.run([exe] + argv[1:], input=raw, stdout=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"error: {argv[0]} failed with exit code {proc.returncode}")
    return proc.stdout


def cpio_entries(data):
    pos = 0
    while True:
        if data[pos:pos + 6] not in CPIO_NEWC:
            break
        if pos + 110 > len(data):
            break
        fields = [int(data[pos + 6 + i * 8:pos + 6 + (i + 1) * 8], 16) for i in range(13)]
        (ino, mode, uid, gid, nlink, mtime, filesize, devmajor, devminor,
         rdevmajor, rdevminor, namesize, check) = fields
        name_start = pos + 110
        name_end = name_start + namesize
        name = data[name_start:name_end - 1].decode("utf-8", "replace")
        data_start = align(name_end, 4)
        file_data = data[data_start:data_start + filesize]
        yield {
            "mode": mode,
            "namesize": namesize,
            "filesize": filesize,
            "name": name,
            "data": file_data,
            "offset": pos,
        }
        pos = data_start + align(filesize, 4)
        if name == "TRAILER!!!":
            break


def extract_cpio(data, dest):
    dest = os.path.abspath(dest)
    count = 0
    for entry in cpio_entries(data):
        name = entry["name"]
        if name in ("TRAILER!!!", ".") or not name:
            continue
        count += 1
        target = os.path.normpath(os.path.join(dest, name))
        if target != dest and not target.startswith(dest + os.sep):
            print(f"skip suspicious path: {name}", file=sys.stderr)
            continue
        mode = entry["mode"]
        ftype = mode & 0o170000
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if ftype == 0o040000:
            os.makedirs(target, exist_ok=True)
        elif ftype == 0o120000:
            link_target = entry["data"].decode("utf-8", "replace")
            if os.path.lexists(target):
                os.unlink(target)
            os.symlink(link_target, target)
        elif ftype == 0o100000:
            with open(target, "wb") as fh:
                fh.write(entry["data"])
            os.chmod(target, mode & 0o777)
            if entry["namesize"] and entry["filesize"] == 0 and entry["mode"] & 0o777:
                print(f"warning: hard link or empty file: {name}", file=sys.stderr)
        elif ftype == 0o020000:
            print(f"skip char device: {name}", file=sys.stderr)
        elif ftype == 0o060000:
            print(f"skip block device: {name}", file=sys.stderr)
        else:
            print(f"skip special file: {name} (mode {oct(mode)})", file=sys.stderr)
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", help="boot or recovery image")
    ap.add_argument("outdir", help="directory for extracted components")
    ap.add_argument("--extract", action="store_true", help="extract the ramdisk cpio")
    ap.add_argument("--no-ramdisk", action="store_true", help="do not decompress the ramdisk")
    args = ap.parse_args()

    with open(args.image, "rb") as fh:
        data = fh.read()

    info = parse_header(data)
    os.makedirs(args.outdir, exist_ok=True)

    page = info["page_size"]
    pieces = [
        ("kernel", info["kernel_offset"], info["kernel_size"]),
        ("ramdisk", info["ramdisk_offset"], info["ramdisk_size"]),
        ("second", info["second_offset"], info["second_size"]),
        ("recovery_dtbo", info["recovery_dtbo_offset_calc"], info["recovery_dtbo_size"]),
        ("dtb", info["dtb_offset"], info["dtb_size"]),
    ]

    print(f"image        : {args.image}")
    print(f"size         : {len(data)} bytes")
    print(f"sha256       : {sha256(data)}")
    print(f"header ver   : {info['header_version']}")
    print(f"os version   : {info['os_version']:#010x}")
    print(f"page size    : {page}")
    for key in ("kernel", "ramdisk", "second"):
        print(f"{key:13s}: offset={info[key + '_offset']:#x} size={info[key + '_size']}")
    print(f"recovery_dtbo: offset={info['recovery_dtbo_offset_calc']:#x} size={info['recovery_dtbo_size']}")
    print(f"dtb          : offset={info['dtb_offset']:#x} size={info['dtb_size']}")
    print(f"name         : {info.get('name', '')}")
    print(f"cmdline      : {info.get('cmdline', '')}")
    if info.get("extra_cmdline"):
        print(f"extra cmdline: {info['extra_cmdline']}")

    for name, offset, size in pieces:
        if size <= 0:
            continue
        blob = data[offset:offset + size]
        if len(blob) != size:
            print(f"warning: {name} is truncated ({len(blob)}/{size})", file=sys.stderr)
        path = os.path.join(args.outdir, name)
        with open(path, "wb") as fh:
            fh.write(blob)
        print(f"wrote {path} ({size} bytes, sha256 {sha256(blob)})")

    if args.no_ramdisk or info["ramdisk_size"] <= 0:
        return

    ramdisk_path = os.path.join(args.outdir, "ramdisk")
    with open(ramdisk_path, "rb") as fh:
        raw = fh.read()
    cpio_path = os.path.join(args.outdir, "ramdisk.cpio")
    kind, unpacked = decompress_ramdisk(raw, cpio_path)
    print(f"ramdisk      : {kind} -> {unpacked} bytes cpio")

    if args.extract:
        with open(cpio_path, "rb") as fh:
            cpio_data = fh.read()
        if cpio_data[:6] not in CPIO_NEWC:
            print("warning: decompressed ramdisk is not a newc cpio archive", file=sys.stderr)
            return
        root = os.path.join(args.outdir, "ramdisk-root")
        if os.path.isdir(root):
            shutil.rmtree(root)
        os.makedirs(root)
        count = extract_cpio(cpio_data, root)
        print(f"extracted    : {count} entries -> {root}")


if __name__ == "__main__":
    main()
