"""Tkinter UI for the EQL Plane of Sky tracker."""
import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import model, parsers, pdfout

APP_TITLE = "EQL Plane of Sky Tracker"

BG = "#1e1f22"
PANEL = "#26282c"
FG = "#e8e8e8"
DIM = "#9aa0a6"
ACCENT = "#c8a24a"
OK = "#5fa85f"
WARN = "#d08a3c"
BAD = "#b45050"


def resource_path(rel):
    """Works both from source and from a PyInstaller one-file bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(here, rel)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 620)
        self.configure(bg=BG)

        self.settings = model.load_settings()
        self.overrides = model.load_overrides()
        # A confirmed folder is remembered. On first run we search and ask.
        self.folder = self.settings.get("folder", "")
        self.character_stem = self.settings.get("character")
        self._needs_confirm = not self.folder
        self.data = model.load_dataset(resource_path(os.path.join("data", "sky.json")))
        self.tracker = model.Tracker(self.data, overrides=self.overrides)
        self.paths = {"achievements": None, "inventory": None,
                      "character": None, "server": None}

        self._style()
        self._build()
        if self._needs_confirm:
            self.after(120, self.detect_install)
        else:
            self.reload(initial=True)

    # ---------------- chrome ----------------

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL)
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=PANEL, foreground=DIM,
                    padding=(16, 8), font=("Segoe UI", 10))
        s.map("TNotebook.Tab", background=[("selected", BG)],
              foreground=[("selected", ACCENT)])
        s.configure("TFrame", background=BG)
        s.configure("Panel.TFrame", background=PANEL)
        s.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        s.configure("Dim.TLabel", foreground=DIM, font=("Segoe UI", 9))
        s.configure("H1.TLabel", font=("Segoe UI Semibold", 15), foreground=FG)
        s.configure("H2.TLabel", font=("Segoe UI Semibold", 11), foreground=ACCENT)
        s.configure("Mono.TLabel", font=("Consolas", 11), foreground=ACCENT,
                    background=PANEL)
        s.configure("TButton", font=("Segoe UI", 9), padding=(10, 5))
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=FG, rowheight=24, font=("Segoe UI", 10),
                    borderwidth=0)
        s.configure("Treeview.Heading", background=BG, foreground=DIM,
                    font=("Segoe UI Semibold", 9), relief="flat")
        s.map("Treeview", background=[("selected", "#3a3f47")])

    def _build(self):
        top = ttk.Frame(self, padding=(14, 10, 14, 6))
        top.pack(fill="x")
        self.lbl_title = ttk.Label(top, text=APP_TITLE, style="H1.TLabel")
        self.lbl_title.pack(side="left")
        self.lbl_who = ttk.Label(top, text="", style="Dim.TLabel")
        self.lbl_who.pack(side="left", padx=(12, 0))

        ttk.Button(top, text="Refresh", command=self.reload).pack(side="right")
        self.var_char = tk.StringVar()
        self.cbo_char = ttk.Combobox(top, textvariable=self.var_char, width=22,
                                     state="readonly")
        self.cbo_char.bind("<<ComboboxSelected>>", self._on_char_change)
        ttk.Button(top, text="Export PDF…", command=self.export_pdf).pack(side="right", padx=6)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self.tab_classes = ttk.Frame(self.nb)
        self.tab_farm = ttk.Frame(self.nb)
        self.tab_zone = ttk.Frame(self.nb)
        self.tab_setup = ttk.Frame(self.nb)
        self.nb.add(self.tab_classes, text="  Class Unlocks  ")
        self.nb.add(self.tab_farm, text="  Farming List  ")
        self.nb.add(self.tab_zone, text="  Zone Guide  ")
        self.nb.add(self.tab_setup, text="  Setup & Help  ")

        self._build_classes()
        self._build_farm()
        self._build_zone()
        self._build_setup()

        bar = ttk.Frame(self, style="Panel.TFrame", padding=(12, 6))
        bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(bar, text="", style="Dim.TLabel",
                                    background=PANEL)
        self.lbl_status.pack(side="left")
        ttk.Label(bar, text="Update with:  %s   +   %s" % model.COMMANDS,
                  style="Dim.TLabel", background=PANEL).pack(side="right")

    # ---------------- tab: classes ----------------

    def _build_classes(self):
        f = self.tab_classes
        left = ttk.Frame(f, padding=(4, 8))
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Closest to unlocking, first",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 4))

        cols = ("progress", "left", "npc", "status")
        self.tv_class = ttk.Treeview(left, columns=cols, show="tree headings", height=18)
        self.tv_class.heading("#0", text="Class")
        self.tv_class.heading("progress", text="Progress")
        self.tv_class.heading("left", text="Left")
        self.tv_class.heading("npc", text="Turn in to")
        self.tv_class.heading("status", text="Status")
        self.tv_class.column("#0", width=130, anchor="w")
        self.tv_class.column("progress", width=170, anchor="w")
        self.tv_class.column("left", width=48, anchor="center")
        self.tv_class.column("npc", width=160, anchor="w")
        self.tv_class.column("status", width=150, anchor="w")
        self.tv_class.pack(fill="both", expand=True)
        self.tv_class.bind("<<TreeviewSelect>>", self._on_class_select)
        self.tv_class.tag_configure("unlocked", foreground=OK)
        self.tv_class.tag_configure("close", foreground=ACCENT)

        right = ttk.Frame(f, style="Panel.TFrame", padding=12, width=430)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)
        self.lbl_detail_head = ttk.Label(right, text="Select a class",
                                         style="H2.TLabel", background=PANEL)
        self.lbl_detail_head.pack(anchor="w")
        self.lbl_detail_npc = ttk.Label(right, text="", style="Dim.TLabel",
                                        background=PANEL)
        self.lbl_detail_npc.pack(anchor="w", pady=(0, 8))
        self.txt_detail = tk.Text(right, wrap="word", bg=PANEL, fg=FG, bd=0,
                                  font=("Segoe UI", 9), padx=2, pady=2,
                                  highlightthickness=0)
        self.txt_detail.pack(fill="both", expand=True)
        self.txt_detail.tag_configure("h", font=("Segoe UI Semibold", 10),
                                      foreground=ACCENT, spacing1=8, spacing3=3)
        self.txt_detail.tag_configure("done", foreground=OK)
        self.txt_detail.tag_configure("ready", foreground=ACCENT,
                                      font=("Segoe UI Semibold", 9))
        self.txt_detail.tag_configure("need", foreground=FG)
        self.txt_detail.tag_configure("dim", foreground=DIM)
        self.txt_detail.configure(state="disabled")

    def _on_class_select(self, _evt=None):
        sel = self.tv_class.selection()
        if not sel:
            return
        name = self.tv_class.item(sel[0], "text").strip()
        cls = next((c for c in self.data["classes"] if c["name"] == name), None)
        if not cls:
            return
        p = self.tracker.class_progress(cls)
        self.lbl_detail_head.configure(text="%s  -  %d of %d Tests"
                                            % (cls["name"], p["done"], p["total"]))
        self.lbl_detail_npc.configure(text="Turn in to %s, in the Efreeti Chamber"
                                           % cls["turnin_npc"])
        t = self.txt_detail
        t.configure(state="normal")
        t.delete("1.0", "end")

        buckets = {model.READY: [], model.PARTIAL: [], model.TODO: [], model.DONE: []}
        for test in cls["tests"]:
            st, have, need = self.tracker.test_status(cls, test)
            buckets[st].append((test, have, need))

        for st in (model.READY, model.PARTIAL, model.TODO, model.DONE):
            rows = buckets[st]
            if not rows:
                continue
            t.insert("end", "%s  (%d)\n" % (model.STATUS_LABEL[st], len(rows)), "h")
            for test, have, need in rows:
                if st == model.DONE:
                    t.insert("end", "   %s  ->  %s\n" % (test["test"], test["reward"]), "done")
                    continue
                tag = "ready" if st == model.READY else "need"
                t.insert("end", "   %s\n" % test["test"], tag)
                t.insert("end", "      reward: %s\n" % test["reward"], "dim")
                t.insert("end", '      hail:   say "%s" to %s\n'
                         % (test.get("trigger", "?"), cls["turnin_npc"]), "dim")
                rc = test.get("rune_classes") or ""
                t.insert("end", "      rune:   %s%s\n"
                         % (test["rune"], ("   [%s]" % rc) if rc else ""), "dim")
                for c in have:
                    t.insert("end", "      HAVE  %s  (%s)\n"
                             % (c["item"], self.tracker.where(c["item"]) or "held"), "done")
                for c in need:
                    t.insert("end", "      NEED  %s  <- %s\n" % (c["item"], c["source"]), "need")
        t.configure(state="disabled")

    # ---------------- tab: farm ----------------

    def _build_farm(self):
        f = self.tab_farm
        head = ttk.Frame(f, padding=(4, 8))
        head.pack(fill="x")
        ttk.Label(head, text="Grouped by what you have to kill. "
                             "Turn-ins consume the component, so x2 means farm it twice.",
                  style="Dim.TLabel").pack(anchor="w")
        ttk.Label(head, text="Double-click an item to mark it as already held "
                             "(a manual override, remembered between sessions).",
                  style="Dim.TLabel").pack(anchor="w")
        cols = ("count", "needed")
        self.tv_farm = ttk.Treeview(f, columns=cols, show="tree headings")
        self.tv_farm.heading("#0", text="Island / Item")
        self.tv_farm.heading("count", text="Qty")
        self.tv_farm.heading("needed", text="Needed by")
        self.tv_farm.column("#0", width=330, anchor="w")
        self.tv_farm.column("count", width=50, anchor="center")
        self.tv_farm.column("needed", width=620, anchor="w")
        self.tv_farm.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        self.tv_farm.tag_configure("island", font=("Segoe UI Semibold", 10),
                                   foreground=ACCENT)
        self.tv_farm.tag_configure("multi", foreground=WARN)
        self.tv_farm.tag_configure("manual", foreground=OK)
        self.tv_farm.bind("<Double-1>", self._toggle_have)

    # ---------------- tab: zone ----------------

    def _build_zone(self):
        f = self.tab_zone
        self.txt_zone = tk.Text(f, wrap="word", bg=PANEL, fg=FG, bd=0,
                                font=("Segoe UI", 10), padx=16, pady=14,
                                highlightthickness=0)
        self.txt_zone.pack(fill="both", expand=True, padx=4, pady=8)
        self.txt_zone.tag_configure("h", font=("Segoe UI Semibold", 12),
                                    foreground=ACCENT, spacing1=12, spacing3=4)
        self.txt_zone.tag_configure("b", font=("Segoe UI Semibold", 10))
        self.txt_zone.tag_configure("dim", foreground=DIM)

    def _fill_zone(self):
        z = self.data["zone"]
        t = self.txt_zone
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", "Getting in\n", "h")
        t.insert("end", "%s\nZone name: %s   Minimum level: %d\n\n"
                 % (z["entry"], z["zone_short"], z["min_level"]))
        t.insert("end", "Turn-ins\n", "h")
        t.insert("end", z["turnin_location"] + "\n\n")
        t.insert("end", "Island progression\n", "h")
        for isl in self.data["islands"]:
            t.insert("end", "%-5s %-16s " % (isl["id"], isl["name"]), "b")
            t.insert("end", "boss: %s" % isl["boss"])
            if isl["needs_key"]:
                t.insert("end", "   (needs %s)" % isl["needs_key"], "dim")
            t.insert("end", "\n")
            if isl["notes"]:
                t.insert("end", "      %s\n" % isl["notes"], "dim")
        t.insert("end", "\nKeys - dropped by the island bosses\n", "h")
        for k in self.data["keys"]:
            t.insert("end", "  %-22s from %-32s opens %s\n"
                     % (k["key"], k.get("from", "?"), k.get("to", "?")))
        t.insert("end", "\nThings that will cost you a trip\n", "h")
        for n in z["notes"]:
            t.insert("end", "  - %s\n" % n)
        t.configure(state="disabled")

    # ---------------- tab: setup ----------------

    def _build_setup(self):
        f = ttk.Frame(self.tab_setup, padding=18)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Step 1 - run these two commands in game",
                  style="H2.TLabel").pack(anchor="w")
        box = ttk.Frame(f, style="Panel.TFrame", padding=14)
        box.pack(fill="x", pady=(6, 4))
        ttk.Label(box, text=model.CMD_ACHIEVEMENTS, style="Mono.TLabel").pack(anchor="w")
        ttk.Label(box, text=model.CMD_INVENTORY, style="Mono.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Button(box, text="Copy both commands",
                   command=self._copy_cmds).pack(anchor="w", pady=(10, 0))
        ttk.Label(f, text="Stand at a banker with the bank window open before running the "
                          "inventory command, or your bank contents may be missing.",
                  style="Dim.TLabel", wraplength=820).pack(anchor="w", pady=(2, 14))

        ttk.Label(f, text="Step 2 - point the tracker at your EverQuest Legends folder",
                  style="H2.TLabel").pack(anchor="w")
        row = ttk.Frame(f)
        row.pack(fill="x", pady=(6, 4))
        self.var_folder = tk.StringVar(value=self.folder)
        e = ttk.Entry(row, textvariable=self.var_folder, font=("Consolas", 9))
        e.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Detect…", command=self.detect_install).pack(side="left", padx=6)
        ttk.Button(row, text="Browse…", command=self._pick_folder).pack(side="left")
        ttk.Button(row, text="Refresh", command=self.reload).pack(side="left", padx=6)

        ttk.Label(f, text="Step 3 - file status", style="H2.TLabel").pack(anchor="w", pady=(14, 0))
        self.lbl_files = ttk.Label(f, text="", style="Dim.TLabel", justify="left")
        self.lbl_files.pack(anchor="w", pady=(4, 14))

        ovr = ttk.Frame(f)
        ovr.pack(fill="x", pady=(0, 12))
        self.lbl_over = ttk.Label(ovr, text="", style="Dim.TLabel")
        self.lbl_over.pack(side="left")
        ttk.Button(ovr, text="Clear manual overrides",
                   command=self._clear_overrides).pack(side="left", padx=10)

        ttk.Label(f, text="How this works", style="H2.TLabel").pack(anchor="w")
        ttk.Label(f, justify="left", wraplength=880, style="Dim.TLabel", text=(
            "The achievements file is the authority for what you have completed - it records what "
            "you OBTAINED, not what you still carry, so rewards you sold or merged away still "
            "count. The inventory file is used only to work out which quest components you are "
            "currently holding.\n\n"
            "Turn-ins consume the component. An item needed by two Tests must be farmed twice.\n\n"
            "Wind Runes drop from every mob in the zone but are class-restricted, so put the "
            "target class in your loadout before farming its rune."
        )).pack(anchor="w", pady=(4, 0))

    def _copy_cmds(self):
        self.clipboard_clear()
        self.clipboard_append("%s\n%s" % model.COMMANDS)
        messagebox.showinfo(APP_TITLE, "Copied:\n\n%s\n%s" % model.COMMANDS)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="Select your EverQuest Legends folder",
                                    initialdir=self.var_folder.get() or "/")
        if d:
            self.var_folder.set(d)
            self.settings["folder"] = d
            model.save_settings(self.settings)
            self.reload()

    def detect_install(self, deep=False):
        """Search for the game folder, then ASK the user to confirm it."""
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            hits = model.find_installs(deep=deep)
        finally:
            self.config(cursor="")

        if not hits:
            if not deep:
                if messagebox.askyesno(
                        APP_TITLE,
                        "No EverQuest Legends folder found in the usual places.\n\n"
                        "Search all drives? This takes a little longer."):
                    return self.detect_install(deep=True)
            messagebox.showinfo(
                APP_TITLE,
                "Could not find the game folder automatically.\n\n"
                "Use Browse… on the Setup & Help tab to point at it yourself.\n"
                "It is the folder containing eqgame.exe.")
            self.nb.select(self.tab_setup)
            self.reload()
            return

        chosen = hits[0] if len(hits) == 1 else _AskFolder(self, hits).result
        if chosen is None:
            self.nb.select(self.tab_setup)
            self.reload()
            return

        if len(hits) == 1:
            found = parsers.find_exports(chosen)
            detail = ("Found these exports:\n    %s\n    %s"
                      % (os.path.basename(found["achievements"]) if found["achievements"]
                         else "(no achievements export yet)",
                         os.path.basename(found["inventory"]) if found["inventory"]
                         else "(no inventory export yet)"))
            if not messagebox.askyesno(
                    APP_TITLE,
                    "Found your EverQuest Legends install here:\n\n%s\n\n%s\n\n"
                    "Is this the right folder?" % (chosen, detail)):
                self.nb.select(self.tab_setup)
                self._pick_folder()
                return

        self.var_folder.set(chosen)
        self.settings["folder"] = chosen
        model.save_settings(self.settings)
        self.reload(initial=True)

    # ---------------- data ----------------

    def reload(self, initial=False):
        self.folder = self.var_folder.get() if hasattr(self, "var_folder") else self.folder
        self.paths = parsers.find_exports(self.folder, self.character_stem)
        if self.paths["stem"]:
            self.character_stem = self.paths["stem"]
            self.settings["character"] = self.character_stem
        ach = parsers.parse_achievements(self.paths["achievements"])
        inv = parsers.parse_inventory(self.paths["inventory"])
        self.tracker = model.Tracker(self.data, ach, inv, self.overrides)

        self.settings["folder"] = self.folder
        model.save_settings(self.settings)

        self._fill_classes()
        self._fill_farm()
        self._fill_zone()
        self._fill_status()

        if not self.paths["achievements"]:
            self.nb.select(self.tab_setup)
            if initial:
                self.after(250, self._first_run_dialog)

    def _first_run_dialog(self):
        messagebox.showwarning(
            APP_TITLE,
            "No achievements export found in:\n%s\n\n%s"
            % (self.folder or "(no folder set)", model.COMMAND_HELP))

    def _fill_status(self):
        bits = []
        for kind in ("achievements", "inventory"):
            p = self.paths[kind]
            when = parsers.file_age(p)
            if when:
                age = datetime.datetime.now() - when
                hrs = age.total_seconds() / 3600.0
                stamp = when.strftime("%d %b %H:%M")
                bits.append("%s: %s%s" % (kind, stamp,
                                          "  (stale)" if hrs > 24 else ""))
            else:
                bits.append("%s: MISSING - run %s" %
                            (kind, model.CMD_ACHIEVEMENTS if kind == "achievements"
                             else model.CMD_INVENTORY))
        self.lbl_status.configure(text="   |   ".join(bits))
        self.lbl_files.configure(text="\n".join(
            "%-14s %s" % (k, self.paths[k] or "not found") for k in ("achievements", "inventory")))

        stems = [c["stem"] for c in parsers.list_characters(self.folder)]
        if len(stems) > 1:
            self.cbo_char["values"] = stems
            self.var_char.set(self.paths.get("stem") or stems[0])
            if not self.cbo_char.winfo_ismapped():
                self.cbo_char.pack(side="right", padx=8)
        elif self.cbo_char.winfo_ismapped():
            self.cbo_char.pack_forget()

        who = self.paths.get("character") or ""
        ach = self.tracker.ach
        extra = []
        if ach.get("race_created"):
            extra.append(ach["race_created"])
        primary = [c for c, r in ach["classes"].items() if r.get("confirmed_primary")]
        if primary:
            extra.append("Primary: " + primary[0])
        s = self.tracker.summary()
        extra.append("%d/%d classes unlocked" % (s["classes_unlocked"], s["classes_total"]))
        extra.append("%d items to farm" % s["items_to_farm"])
        self.lbl_who.configure(text=("%s   %s" % (who, " · ".join(extra))).strip())

    def _on_char_change(self, _evt=None):
        self.character_stem = self.var_char.get()
        self.settings["character"] = self.character_stem
        model.save_settings(self.settings)
        self.reload()

    def _toggle_have(self, _evt=None):
        """Double-click a farm row to mark that component as already held."""
        sel = self.tv_farm.selection()
        if not sel:
            return
        item = self.tv_farm.item(sel[0], "text").strip()
        if not item or self.tv_farm.parent(sel[0]) == "":
            return
        key = "have:" + item
        if self.overrides.pop(key, None) is None:
            self.overrides[key] = True
        model.save_overrides(self.overrides)
        self.reload()

    def _clear_overrides(self):
        if not self.overrides:
            messagebox.showinfo(APP_TITLE, "No manual overrides are set.")
            return
        if messagebox.askyesno(APP_TITLE, "Clear %d manual override(s)?"
                                          % len(self.overrides)):
            self.overrides = {}
            model.save_overrides(self.overrides)
            self.reload()

    def _fill_classes(self):
        tv = self.tv_class
        tv.delete(*tv.get_children())
        for r in self.tracker.all_progress():
            filled = int(round(10.0 * r["done"] / max(1, r["total"])))
            bar = "█" * filled + "░" * (10 - filled)
            if r["confirmed_primary"]:
                status = "PRIMARY CLASS"
            elif r["unlocked"]:
                status = "UNLOCKED" + (" (token)" if r["token_used"] else "")
            elif r["ready"]:
                status = "%d ready to turn in" % r["ready"]
            else:
                status = ""
            tags = ("unlocked",) if r["unlocked"] else (
                ("close",) if r["remaining"] <= 1 else ())
            tv.insert("", "end", text="  " + r["name"], tags=tags, values=(
                "%s  %d/%d" % (bar, r["done"], r["total"]),
                "" if r["unlocked"] else r["remaining"],
                r["npc"], status))
        kids = tv.get_children()
        if kids:
            tv.selection_set(kids[0])

    def _fill_farm(self):
        tv = self.tv_farm
        tv.delete(*tv.get_children())
        for iid, items in self.tracker.farm_list().items():
            isl = self.tracker.island_by_id(iid)
            label = "%s  %s" % (isl["id"], isl["name"])
            if isl.get("boss"):
                label += "   -   %s" % isl["boss"]
            parent = tv.insert("", "end", text=label, tags=("island",),
                               values=(len(items), isl.get("notes", "")[:150]), open=True)
            for it in items:
                users = "; ".join("%s %s" % (c, t) for c, t in it["needed_by"])
                tv.insert(parent, "end", text="      " + it["item"],
                          tags=("multi",) if it["count"] > 1 else (),
                          values=("x%d" % it["count"] if it["count"] > 1 else "1", users))
        for item in sorted(k[5:] for k in self.overrides if k.startswith("have:")):
            tv.insert("", "end", text="  (manual) " + item, tags=("manual",),
                      values=("held", "marked by you - double-click to undo"))

    # ---------------- export ----------------

    def export_pdf(self):
        if not self.tracker.has_achievements():
            if not messagebox.askyesno(
                    APP_TITLE,
                    "No achievements data loaded, so the report will be incomplete.\n\n%s\n\n"
                    "Export anyway?" % model.COMMAND_HELP):
                return
        which = _AskReport(self).result
        if not which:
            return
        default = "PlaneOfSky_%s_%s.pdf" % (
            self.paths.get("character") or "character",
            datetime.date.today().isoformat())
        path = filedialog.asksaveasfilename(
            title="Save PDF", defaultextension=".pdf", initialfile=default,
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            pdfout.export(self.tracker, path, which)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, "PDF export failed:\n%s" % exc)
            return
        if messagebox.askyesno(APP_TITLE, "Saved:\n%s\n\nOpen it now?" % path):
            try:
                os.startfile(path)
            except Exception:
                pass


class _AskFolder(tk.Toplevel):
    """Modal: more than one candidate install was found - which one?"""

    def __init__(self, parent, candidates):
        super().__init__(parent)
        self.result = None
        self.title("Confirm game folder")
        self.configure(bg=BG)
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text="Found more than one EverQuest Legends folder",
                  style="H2.TLabel").pack(anchor="w", padx=18, pady=(16, 2))
        ttk.Label(self, text="Pick the one you play on.",
                  style="Dim.TLabel").pack(anchor="w", padx=18, pady=(0, 10))
        for path in candidates:
            found = parsers.find_exports(path)
            note = "  (exports found)" if found["achievements"] else "  (no exports yet)"
            ttk.Button(self, text=path + note, width=76,
                       command=lambda p=path: self._pick(p)).pack(padx=18, pady=2, anchor="w")
        ttk.Button(self, text="None of these - let me browse",
                   command=lambda: self._pick("")).pack(padx=18, pady=(10, 16), anchor="w")
        self.grab_set()
        parent.wait_window(self)

    def _pick(self, p):
        self.result = p or None
        self.destroy()


class _AskReport(tk.Toplevel):
    """Small modal: which report to export."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Export PDF")
        self.configure(bg=BG)
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text="Which report?", style="H2.TLabel").pack(
            anchor="w", padx=18, pady=(16, 8))
        for key, label in (("classes", "Class unlock progress + outstanding Tests"),
                           ("farm", "Farming list, grouped by boss"),
                           ("all", "Both (full report)")):
            ttk.Button(self, text=label, width=46,
                       command=lambda k=key: self._pick(k)).pack(padx=18, pady=3)
        ttk.Button(self, text="Cancel", command=self.destroy).pack(padx=18, pady=(8, 16))
        self.grab_set()
        parent.wait_window(self)

    def _pick(self, k):
        self.result = k
        self.destroy()


def main():
    App().mainloop()
