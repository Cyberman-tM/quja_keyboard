# boQwI' dictionary data

This folder contains a small standard-library-only downloader for the public
Klingon data maintained by De7vID for boQwI'. The upstream repository is
licensed under Apache-2.0; keep its `LICENSE` and attribution files with any
redistributed copy.

## Download and build the local copy

This machine has Python 3.14.7 installed at
`C:\Users\chris\AppData\Local\Python\bin\python.exe`. The plain `python`
command currently resolves to a Windows app-execution alias first, so run the
downloader from this folder with:

```powershell
& 'C:\Users\chris\AppData\Local\Python\bin\python.exe' .\download_dictionary.py
```

The command downloads the current `main` branch snapshot into `source/`, writes
`entries.csv`, and records the upstream version and entry counts in
`download_metadata.json`. Re-running it refreshes the local snapshot. To put
the generated data elsewhere, pass `--output`, for example:

```powershell
& 'C:\Users\chris\AppData\Local\Python\bin\python.exe' .\download_dictionary.py --output ..\..\..\..\..\klingon-dictionary
```

`entries.csv` is UTF-8 with a byte-order mark for spreadsheet compatibility.
Each row represents one dictionary entry, with `entry_name` read from the YAML
content, category, part of speech, source path, entry number within that file,
and the full original YAML text. A YAML file can contain multiple homophones,
so CSV rows can repeat the source file. Keeping the original YAML intact
preserves nested fields, translations, and upstream changes without requiring
a YAML package. For structured field-level access, use the original files
under `source/entries/` with a YAML parser in the consuming project. Use
`--offline` to rebuild the index from the local snapshot without downloading.

The current flat index has 6,531 dictionary entries across 6,264 YAML files.
The source repository is undergoing a schema migration, so the importer keeps
the original files as the canonical local copy instead of translating them
into a narrower custom schema. This download script does not modify the
keyboard pack. Windows-forbidden characters in upstream filenames are
percent-encoded in `source/`. Names that differ only by letter case get a
`~case2` suffix (or the next available number) where needed. `path_map.json`
records changed paths; the CSV keeps the original paths and names.
