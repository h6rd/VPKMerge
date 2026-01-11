# Build: pyinstaller --onefile --console --collect-all vpk --collect-all send2trash --collect-all rich --name "VPKMerge" --icon=icon.ico VPKMerge.py

import os
import glob
import shutil
import time
import vpk
from send2trash import send2trash
from rich.console import Console
from rich.text import Text


def print_ascii_art(console):
    PURPLE = "#B486FF"
    WHITE = "white"

    art = Text()
    art.append("██╗   ██╗██████╗ ██╗  ██╗", style=PURPLE)
    art.append("███╗   ███╗███████╗██████╗  ██████╗ ███████╗\n", style=WHITE)
    art.append("██║   ██║██╔══██╗██║ ██╔╝", style=PURPLE)
    art.append("████╗ ████║██╔════╝██╔══██╗██╔════╝ ██╔════╝\n", style=WHITE)
    art.append("██║   ██║██████╔╝█████╔╝ ", style=PURPLE)
    art.append("██╔████╔██║█████╗  ██████╔╝██║  ███╗█████╗  \n", style=WHITE)
    art.append("██║   ██║██╔═══╝ ██╔═██╗ ", style=PURPLE)
    art.append("██║╚██╔╝██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  \n", style=WHITE)
    art.append("╚██████╔╝██║     ██║  ██╗", style=PURPLE)
    art.append("██║ ╚═╝ ██║███████╗██║  ██║╚██████╔╝███████╗\n", style=WHITE)
    art.append(" ╚═════╝ ╚═╝     ╚═╝  ╚═╝", style=PURPLE)
    art.append("╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝\n", style=WHITE)
    art.append("                      by @", style=WHITE)
    art.append("dota2", style=WHITE)
    art.append("pornfx", style=PURPLE)

    console.print(art)


def should_skip_file(file_path):
    filename = os.path.basename(file_path)

    if '"' in filename:
        return True

    return False


def extract_vpk(vpk_path, output_dir):
    try:
        skipped_files = []
        extracted_files = []

        with vpk.open(vpk_path) as vpk_file:
            for file_path in vpk_file:
                if should_skip_file(file_path):
                    skipped_files.append(file_path)
                    continue

                try:
                    file_data = vpk_file.get_file(file_path)
                    full_path = os.path.join(output_dir, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "wb") as f:
                        f.write(file_data.read())
                    extracted_files.append(file_path)
                except Exception as e:
                    skipped_files.append(file_path)

        return True, skipped_files, len(extracted_files)
    except Exception as e:
        return False, [], 0


def main():
    console = Console()

    print_ascii_art(console)

    vpks = glob.glob("*.vpk")

    if not vpks:
        console.print("No VPK files found in the current directory.", style="red")
        return

    temp_dir = "temp"

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    os.makedirs(temp_dir)

    total_skipped = 0
    total_extracted = 0

    for vpk_file in vpks:
        console.print(Text(f"Extracting {os.path.basename(vpk_file)}", style="white"))
        success, skipped_files, extracted_count = extract_vpk(vpk_file, temp_dir)

        if success:
            total_extracted += extracted_count
            total_skipped += len(skipped_files)

            if skipped_files:
                console.print(
                    Text(
                        f"  Skipped {len(skipped_files)} useless files",
                        style="yellow",
                    )
                )
                for i, skipped in enumerate(skipped_files[:3]):
                    console.print(Text(f"    - {skipped}", style="dim yellow"))
                if len(skipped_files) > 3:
                    console.print(
                        Text(
                            f"    ... and {len(skipped_files) - 3} more",
                            style="dim yellow",
                        )
                    )

            console.print(Text(f"  Extracted {extracted_count} files", style="green"))
            send2trash(vpk_file)
        else:
            console.print(Text(f"Failed to extract {vpk_file}", style="red"))

    if total_skipped > 0:
        console.print(Text(f"\nTotal files skipped: {total_skipped}", style="yellow"))
    console.print(Text(f"Total files extracted: {total_extracted}", style="green"))

    output_vpk = "pak10_dir.vpk"
    console.print(Text("Creating combined VPK file", style="cyan"))

    try:
        newpak = vpk.new(temp_dir)
        newpak.save(output_vpk)
    except Exception as e:
        console.print(Text(f"Error creating VPK: {str(e)}", style="red"))
        return

    shutil.rmtree(temp_dir)

    success_text = Text()
    success_text.append("\nSuccess created ", style="green")
    success_text.append(output_vpk, style="white")
    console.print(success_text)

    time.sleep(3)


if __name__ == "__main__":
    main()
