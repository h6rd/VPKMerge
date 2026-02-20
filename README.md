# VPKMerge

A Tool for merging VPK archives

---

## Download
| Platform | Link |
|----------|------|
| Windows  | [VPKMerge-Win.zip](https://github.com/h6rd/VPKMerge/releases/latest/download/VPKMerge-Win.zip) |
| Linux    | [VPKMerge-Linux.zip](https://github.com/h6rd/VPKMerge/releases/latest/download/VPKMerge-Linux.zip) |

---

## Usage

Place the `.vpk` in a folder next to the script and run it

Result will be a file named `pak10_dir.vpk`

---

## Notes

- If the vpk name begins with !, it will be unpacked last in order to overwrite some files for [Dota2PornFxWeb](https://h6rd.github.io/Dota2PornFxWeb/)

---

## Built with

| Library | Purpose |
|---|---|
| [vpk](https://pypi.org/project/vpk/) | Reading and writing VPK archives |
| [rich](https://pypi.org/project/rich/) | Terminal formatting and colored output |