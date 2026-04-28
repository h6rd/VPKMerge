import os
import glob
import shutil
import time
import random
import struct
import zlib
import vpk

try:
    from rich.console import Console
    from rich.text import Text

    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


def print_ascii_art():
    if HAS_RICH:
        width = console.size.width
        PURPLE = "#B486FF"
        WHITE = "white"

        lines = [
            "██╗   ██╗██████╗ ██╗  ██╗███╗   ███╗███████╗██████╗  ██████╗ ███████╗",
            "██║   ██║██╔══██╗██║ ██╔╝████╗ ████║██╔════╝██╔══██╗██╔════╝ ██╔════╝",
            "██║   ██║██████╔╝█████╔╝ ██╔████╔██║█████╗  ██████╔╝██║  ███╗█████╗  ",
            "╚██╗ ██╔╝██╔═══╝ ██╔═██╗ ██║╚██╔╝██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ",
            " ╚████╔╝ ██║     ██║  ██╗██║ ╚═╝ ██║███████╗██║  ██║╚██████╔╝███████╗",
            "  ╚═══╝  ╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝",
            "by @dota2pornfx",
        ]

        console.print()
        for line in lines[:-1]:
            console.print(Text(line.center(width), style=PURPLE))
        console.print(Text(lines[-1].center(width), style=WHITE))
        console.print()
    else:
        print("=" * 10)
        print("VPKMerge")
        print("by @dota2pornfx")
        print("=" * 10 + "\n")


def rprint(msg, style="white"):
    if HAS_RICH:
        console.print(Text(msg, style=style))
    else:
        print(msg)


# Extract
def should_skip_file(file_path):
    filename = os.path.basename(file_path)
    if '"' in filename:
        return True
    return False


def extract_vpk(vpk_path, output_dir, seen_files):
    skipped_files = []
    extracted_files = []

    try:
        with vpk.open(vpk_path) as pak:
            file_list = list(pak)

        with vpk.open(vpk_path) as pak:
            for file_path in file_list:
                if should_skip_file(file_path):
                    skipped_files.append(file_path)
                    continue

                norm = file_path.replace("\\", "/").lower()
                seen_files[norm] = os.path.basename(vpk_path)

                try:
                    data = pak.get_file(file_path).read()
                    full_path = os.path.join(output_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        f.write(data)
                    extracted_files.append(file_path)
                except Exception:
                    skipped_files.append(file_path)

        return True, skipped_files, len(extracted_files)
    except Exception:
        return False, [], 0


# vpk writer
VPK_MAGIC = 0x55AA1234
VPK_VERSION = 1
MAX_ARCHIVE_BYTES = 200 * 1024 * 1024  # 200 MB per chunk


def _vpk_crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _encode_str(s: str) -> bytes:
    return s.encode("utf-8") + b"\x00"


def build_vpk(source_dir: str, output_dir_vpk: str) -> tuple[bool, str]:

    if output_dir_vpk.endswith("_dir.vpk"):
        archive_base = output_dir_vpk[:-8]
    else:
        archive_base = output_dir_vpk[:-4]

    tree: dict[str, dict[str, dict[str, tuple]]] = {}

    archives: list[bytearray] = []
    current_archive = bytearray()
    current_archive_idx = 0

    try:
        for dirpath, dirnames, filenames in os.walk(source_dir):
            dirnames.sort()
            for fn in sorted(filenames):
                full_path = os.path.join(dirpath, fn)
                rel_path = os.path.relpath(full_path, source_dir).replace("\\", "/")

                dot = rel_path.rfind(".")
                if dot != -1 and "/" not in rel_path[dot:]:
                    ext = rel_path[dot + 1 :]
                    path_and_name = rel_path[:dot]
                else:
                    ext = " "
                    path_and_name = rel_path

                slash = path_and_name.rfind("/")
                if slash == -1:
                    vpath = " "
                    vname = path_and_name
                else:
                    vpath = path_and_name[:slash]
                    vname = path_and_name[slash + 1 :]

                with open(full_path, "rb") as f:
                    data = f.read()

                crc = _vpk_crc32(data)
                length = len(data)

                if (
                    len(current_archive) + length > MAX_ARCHIVE_BYTES
                    and len(current_archive) > 0
                ):
                    archives.append(bytes(current_archive))
                    current_archive = bytearray()
                    current_archive_idx += 1

                offset = len(current_archive)
                current_archive.extend(data)

                tree.setdefault(ext, {}).setdefault(vpath, {})[vname] = (
                    current_archive_idx,
                    offset,
                    length,
                    crc,
                )

        if current_archive:
            archives.append(bytes(current_archive))

    except Exception as e:
        return False, f"Error reading source files: {e}"

    tree_buf = bytearray()
    for ext in sorted(tree):
        tree_buf += _encode_str(ext)
        for vpath in sorted(tree[ext]):
            tree_buf += _encode_str(vpath)
            for vname, (arch_idx, offset, length, crc) in sorted(
                tree[ext][vpath].items()
            ):
                tree_buf += _encode_str(vname)
                tree_buf += struct.pack(
                    "<I H H I I H", crc, 0, arch_idx, offset, length, 0xFFFF
                )
            tree_buf += b"\x00"
        tree_buf += b"\x00"
    tree_buf += b"\x00"

    try:
        with open(output_dir_vpk, "wb") as f:
            f.write(struct.pack("<I I I", VPK_MAGIC, VPK_VERSION, len(tree_buf)))
            f.write(tree_buf)
    except Exception as e:
        return False, f"Error writing dir file: {e}"

    try:
        for i, chunk in enumerate(archives):
            archive_path = f"{archive_base}_{i:03d}.vpk"
            with open(archive_path, "wb") as f:
                f.write(chunk)
    except Exception as e:
        return False, f"Error writing archive chunk: {e}"

    total_files = sum(len(names) for ext in tree.values() for names in ext.values())
    size_mb = os.path.getsize(output_dir_vpk) / (1024 * 1024)
    return True, (
        f"{total_files} files, {len(archives)} archive chunk(s), "
        f"dir size {size_mb:.2f} MB"
    )


def verify_vpk(vpk_path: str) -> tuple[bool, str]:
    try:
        with vpk.open(vpk_path) as pak:
            all_files = list(pak)

        if not all_files:
            return False, "VPK contains no files"

        sample = random.sample(
            all_files, min(max(10, len(all_files) // 10), len(all_files))
        )

        with vpk.open(vpk_path) as pak:
            for vpath in sample:
                try:
                    pak.get_file(vpath).read()
                except Exception as e:
                    return False, f"Cannot read '{vpath}': {e}"

        return True, f"{len(all_files)} files indexed, {len(sample)} spot-checked OK"
    except Exception as e:
        return False, str(e)


def main():
    print_ascii_art()

    vpks = glob.glob("*.vpk")
    vpks.sort(
        key=lambda x: (
            not os.path.basename(x).startswith("!"),
            os.path.basename(x).lower(),
        )
    )

    if not vpks:
        rprint("No VPK files found in the current directory.", style="red")
        return

    temp_dir = "temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    seen_files = {}
    total_skipped = 0
    total_extracted = 0

    for vpk_file in vpks:
        rprint(f"Extracting {os.path.basename(vpk_file)}", style="white")
        success, skipped_files, extracted_count = extract_vpk(
            vpk_file, temp_dir, seen_files
        )

        if success:
            total_extracted += extracted_count
            total_skipped += len(skipped_files)

            if skipped_files:
                rprint(f"  Skipped {len(skipped_files)} useless files", style="yellow")
                for s in skipped_files[:3]:
                    rprint(f"    - {s}", style="yellow")
                if len(skipped_files) > 3:
                    rprint(f"    ... and {len(skipped_files) - 3} more", style="yellow")

            rprint(f"  Extracted {extracted_count} files", style="green")
            os.remove(vpk_file)
        else:
            rprint(f"Failed to extract {vpk_file}", style="red")

    if total_skipped > 0:
        rprint(f"\nTotal files skipped: {total_skipped}", style="yellow")
    rprint(f"Total files extracted: {total_extracted}", style="green")

    output_vpk = "pak10_dir.vpk"
    rprint("\nCreating combined VPK file...", style="cyan")

    ok, msg = build_vpk(temp_dir, output_vpk)

    shutil.rmtree(temp_dir)

    if not ok:
        rprint(f"Error creating VPK: {msg}", style="red")
        time.sleep(3)
        return

    rprint(f"Built: {msg}", style="dim green")

    v_ok, v_msg = verify_vpk(output_vpk)
    if v_ok:
        if HAS_RICH:
            t = Text()
            t.append("\nSuccess created ", style="green")
            t.append(output_vpk, style="white")
            console.print(t)
        else:
            print(f"\nSuccess created {output_vpk}")
        rprint(f"Verified: {v_msg}", style="dim green")
    else:
        rprint(f"\nWarning: VPK created but verification failed: {v_msg}", style="red")

    time.sleep(3)


if __name__ == "__main__":
    main()
