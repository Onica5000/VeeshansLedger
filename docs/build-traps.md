# Build traps

Moved out of `CLAUDE.md` on 2026-09-02 to cut per-message preload cost. These matter only when building the exe, not on every message. **Nothing was removed or softened.**

**PyInstaller must be >= 6.22.** Python 3.14 ships **Tcl/Tk 9.0**, whose library lives in
`C:\Python314\tcl\libtcl9.0.4.zip` rather than the old `tcl8.6\` directory tree.
PyInstaller <= 6.20 emits a `_tcl_data` path it never populates, and the built exe dies at
launch with:

```
Failed to execute script 'pyi_rth__tkinter' ... Tcl data directory "...\_MEI...\_tcl_data" not found
```

6.22.2 detects Tcl 9 correctly (`tcl_data_missing: False`, zero separate data files - the DLL
loads its own zip). The build script enforces this version floor and refuses to run below it.

**Smoke-testing a one-file build: check the WINDOW, not the process.** Two traps here:

1. A PyInstaller one-file exe spawns a **child** process that owns the GUI. Enumerating windows
   for the pid returned by `Start-Process` finds nothing. Match on the process *name* instead.
2. "Process still alive after N seconds" passes even when the app is showing a fatal-error
   dialog - that dialog is what keeps it alive. **Assert on the window title.** This bit twice:
   once on the Tcl/Tk 9 crash, and again when a screenshot script reported "captured" for six
   tabs that were all the crash dialog. Any capture or smoke tooling MUST check the title text,
   not merely that a window exists.

```powershell
$t = @(Get-Process VeeshansLedger | ? {$_.MainWindowTitle} | % {$_.MainWindowTitle})
if ($t -match "Veeshan") { "PASS" } else { "FAIL" }
```

If a build fails mysteriously, rebuild with `--console` instead of `--windowed` - the traceback
goes to stdout instead of a dialog.

**Delete `dist\VeeshansLedger.exe` before rebuilding.** A still-running instance locks it and
PyInstaller fails with `PermissionError: [WinError 5]`, which is easy to miss in the log tail.
