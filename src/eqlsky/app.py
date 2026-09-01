"""Tkinter UI for Veeshan's Ledger - an EverQuest Legends quest tracker."""
import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import model, parsers, pdfout

APP_TITLE = "Veeshan's Ledger"
APP_SUB = "EverQuest Legends  ·  Plane of Sky & class epics"

BG = "#17181b"          # window ground
PANEL = "#1e2024"       # content surface
PANEL2 = "#262930"      # headers and insets
LINE = "#33373e"        # borders
SEL = "#3a3f4a"         # neutral selection - a saturated one fights the amber
FG = "#e6e8ea"          # 13.3:1
DIM = "#a8b0ba"         # 7.5:1
ACCENT = "#d4a54a"      # 7.2:1
OK = "#6bbf6b"          # 7.2:1
WARN = "#e0a244"        # 7.3:1
BAD = "#e06c6c"         # 5.1:1 - was #b45050 at 2.96:1, which failed AA


def resource_path(rel):
    """Works both from source and from a PyInstaller one-file bundle."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, rel)
    here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(here, rel)


ROW_ALT = "#24272d"          # ~5% off PANEL - any closer and the stripe vanishes


def _stripe(tv):
    """Alternating row backgrounds. Call _restripe(tv) after (re)filling."""
    tv.tag_configure("odd", background=ROW_ALT)
    tv.tag_configure("even", background=PANEL)


def _restripe(tv):
    """Re-apply stripes over whatever tags a row already carries."""
    for i, iid in enumerate(tv.get_children("")):
        tags = [t for t in tv.item(iid, "tags") if t not in ("odd", "even")]
        tv.item(iid, tags=tags + ["odd" if i % 2 else "even"])


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
        try:
            self.epic_data = model.load_dataset(
                resource_path(os.path.join("data", "epics.json")))
        except Exception:
            self.epic_data = None          # epics dataset is optional
        self.epics = (model.EpicTracker(self.epic_data, overrides=self.overrides)
                      if self.epic_data else None)
        self.paths = {"achievements": None, "inventory": None,
                      "character": None, "server": None}
        self.index = []

        self._dark_titlebar()
        self._style()
        self._build()
        self.bind_all("<Control-f>", self._focus_search)
        if self._needs_confirm:
            self.after(120, self.detect_install)
        else:
            self.reload(initial=True)

    def _dark_titlebar(self):
        """Windows 10 2004+ dark title bar. Harmless no-op elsewhere."""
        try:
            import ctypes
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            pass

    # ---------------- chrome ----------------

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", background=BG, foreground=FG, fieldbackground=PANEL)
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG, foreground=DIM,
                    padding=(16, 8), borderwidth=0, font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", PANEL), ("active", PANEL2)],
              foreground=[("selected", ACCENT), ("active", FG)],
              padding=[("selected", (16, 8, 16, 8))],   # the actual fix for the 3D look
              expand=[("selected", (0, 0, 0, 0))],
              lightcolor=[("selected", PANEL)],
              bordercolor=[("selected", PANEL)])
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
                    foreground=FG, rowheight=26, font=("Segoe UI", 10),
                    borderwidth=0, relief="flat")
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        s.configure("Treeview.Heading", background=PANEL2, foreground=DIM,
                    font=("Segoe UI Semibold", 10), relief="flat",
                    borderwidth=0, padding=(8, 6))
        s.map("Treeview.Heading", background=[("active", LINE)],
              relief=[("active", "flat"), ("pressed", "flat")])
        s.map("Treeview", background=[("selected", SEL)],
              foreground=[("selected", FG)])
        s.configure("Treeview", rowheight=26)
        s.configure("Warn.TFrame", background="#3a2f22")
        s.configure("WarnHead.TLabel", background="#3a2f22", foreground="#e8b45a",
                    font=("Segoe UI Semibold", 11))
        s.configure("WarnBody.TLabel", background="#3a2f22", foreground="#d8d2c8",
                    font=("Segoe UI", 9))
        s.configure("Ck.TCheckbutton", background=BG, foreground=FG,
                    font=("Segoe UI", 9))
        s.configure("Sub.TLabel", foreground=DIM, font=("Segoe UI", 10))
        s.configure("Next.TFrame", background="#20302a")
        s.configure("Next.TLabel", background="#20302a", foreground="#8fd39a",
                    font=("Segoe UI Semibold", 10))
        s.configure("StatK.TLabel", foreground=DIM, font=("Segoe UI", 8))
        s.configure("StatV.TLabel", foreground=FG, font=("Segoe UI Semibold", 11))
        s.configure("StatVa.TLabel", foreground=ACCENT, font=("Segoe UI Semibold", 11))
        s.configure("Bar.TFrame", background=PANEL2)
        s.configure("Bar.TLabel", background=PANEL2, foreground=DIM,
                    font=("Segoe UI", 9))
        s.configure("Who.TLabel", foreground=FG, font=("Segoe UI", 10))
        s.configure("Link.TLabel", foreground=ACCENT, font=("Segoe UI", 9))
        # headings left-aligned to match the cells beneath them
        s.configure("Treeview.Heading", anchor="w", padding=(6, 5))
        s.map("Treeview.Heading", background=[("active", PANEL)])

    def _build(self):
        top = ttk.Frame(self, padding=(16, 12, 16, 4))
        top.pack(fill="x")
        idline = ttk.Frame(top)
        idline.pack(fill="x")
        self.lbl_title = ttk.Label(idline, text=APP_TITLE, style="H1.TLabel")
        self.lbl_title.pack(side="left")
        ttk.Button(idline, text="Refresh", command=self.reload).pack(side="right")
        ttk.Button(idline, text="Export PDF…",
                   command=self.export_pdf).pack(side="right", padx=8)
        self.var_char = tk.StringVar()
        self.cbo_char = ttk.Combobox(idline, textvariable=self.var_char, width=22,
                                     state="readonly")
        self.cbo_char.bind("<<ComboboxSelected>>", self._on_char_change)

        self.stats = ttk.Frame(top)
        self.stats.pack(fill="x", pady=(6, 0))
        self._stat_cells = {}

        # P1: the app already knows what is actionable - say it out loud, on every tab.
        self.frm_next = ttk.Frame(self, style="Next.TFrame", padding=(16, 7))
        self.lbl_next = ttk.Label(self.frm_next, text="", style="Next.TLabel",
                                  cursor="hand2")
        self.lbl_next.pack(anchor="w")
        self.lbl_next.bind("<Button-1>", lambda _e: self.nb.select(self.tab_classes))

        self.frm_next.pack(fill="x", padx=16, pady=(8, 0))

        bar = ttk.Frame(self, style="Bar.TFrame", padding=(14, 7))
        bar.pack(fill="x", side="bottom")
        self.lbl_status = ttk.Label(bar, text="", style="Bar.TLabel")
        self.lbl_status.pack(side="left")
        self.lbl_cmds = ttk.Label(bar, text="Update with:  %s   +   %s" % model.COMMANDS,
                                  style="Bar.TLabel", cursor="hand2")
        self.lbl_cmds.pack(side="right")
        self.lbl_cmds.bind("<Button-1>", lambda _e: self._copy_cmds())

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(6, 4))

        self.tab_search = ttk.Frame(self.nb)
        self.tab_classes = ttk.Frame(self.nb)
        self.tab_farm = ttk.Frame(self.nb)
        self.tab_zone = ttk.Frame(self.nb)
        self.tab_epics = ttk.Frame(self.nb)
        self.tab_setup = ttk.Frame(self.nb)
        self.nb.add(self.tab_search, text="  Search  ")
        self.nb.add(self.tab_classes, text="  Class Unlocks  ")
        self.nb.add(self.tab_farm, text="  Farming List  ")
        self.nb.add(self.tab_zone, text="  Zone Guide  ")
        self.nb.add(self.tab_epics, text="  Epic Quests  ")
        self.nb.add(self.tab_setup, text="  Setup & Help  ")

        self._build_search()
        self._build_classes()
        self._build_farm()
        self._build_zone()
        if self.epic_data:
            self._build_epics()
        else:
            self.nb.forget(self.tab_epics)
        self._build_setup()

        self.nb.select(self.tab_classes)      # land on something useful, not an empty table

        # Screenshot/debug hook: VL_TAB=epics opens that tab directly, so capture
        # tooling never has to synthesise clicks (which can land in other windows).
        want = os.environ.get("VL_TAB", "").strip().lower()
        if want:
            for frame, name in ((self.tab_search, "search"),
                                (self.tab_classes, "classes"),
                                (self.tab_farm, "farming"),
                                (self.tab_zone, "zone"),
                                (self.tab_epics, "epics"),
                                (self.tab_setup, "setup")):
                if name == want and str(frame) in self.nb.tabs():
                    self.nb.select(frame)
                    break


    # ---------------- tab: classes ----------------

    def _build_classes(self):
        f = self.tab_classes
        left = ttk.Frame(f, padding=(4, 8))
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Closest to unlocking, first",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 4))

        cols = ("left", "progress", "status", "npc")
        self.tv_class = ttk.Treeview(left, columns=cols, show="tree headings", height=17)
        self.tv_class.heading("#0", text="Class")
        self.tv_class.heading("left", text="Left")
        self.tv_class.heading("progress", text="Tests")
        self.tv_class.heading("status", text="Status")
        self.tv_class.heading("npc", text="Turn in to")
        self.tv_class.column("#0", width=150, anchor="w")
        self.tv_class.column("left", width=60, anchor="center")
        self.tv_class.column("progress", width=150, anchor="w")
        self.tv_class.column("status", width=170, anchor="w")
        self.tv_class.column("npc", width=170, anchor="w")
        self.tv_class.pack(fill="x")
        self.tv_class.bind("<<TreeviewSelect>>", self._on_class_select)

        ttk.Label(left, text="Ready to turn in now",
                  style="H2.TLabel").pack(anchor="w", pady=(14, 2))
        ttk.Label(left, text="Every Test whose components you already hold, across all classes.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 4))
        rcols = ("test", "npc", "hail", "reward")
        self.tv_ready = ttk.Treeview(left, columns=rcols, show="tree headings", height=7)
        self.tv_ready.heading("#0", text="Class")
        for c, t, w in (("test", "Test", 190), ("npc", "Turn in to", 170),
                        ("hail", "Say", 120), ("reward", "Reward", 200)):
            self.tv_ready.heading(c, text=t)
            self.tv_ready.column(c, width=w, anchor="w")
        self.tv_ready.column("#0", width=150, anchor="w")
        self.tv_ready.pack(fill="both", expand=True)
        _stripe(self.tv_ready)
        self.tv_ready.tag_configure("none", foreground=DIM)
        _stripe(self.tv_class)
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

    def _fill_ready(self):
        tv = self.tv_ready
        tv.delete(*tv.get_children())
        rows = []
        for cls in self.tracker.data["classes"]:
            for t in cls["tests"]:
                if self.tracker.test_status(cls, t)[0] == model.READY:
                    rows.append((cls, t))
        if not rows:
            tv.insert("", "end", text="  —", tags=("none",),
                      values=("Nothing is ready to turn in yet", "", "", ""))
            return
        for cls, t in rows:
            tv.insert("", "end", text="  " + cls["name"], values=(
                t["test"], cls["turnin_npc"],
                '"%s"' % t.get("trigger", ""), t["reward"]))
        _restripe(tv)

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
        _stripe(self.tv_farm)
        self.tv_farm.tag_configure("island", font=("Segoe UI Semibold", 10),
                                   foreground=ACCENT)
        self.tv_farm.tag_configure("multi", foreground=WARN)
        self.tv_farm.tag_configure("manual", foreground=OK)
        self.tv_farm.bind("<Double-1>", self._toggle_have)
        self.tv_farm.bind("<<TreeviewSelect>>", self._on_farm_select)

        # Boss mechanics used to be crammed into a table column and were cut off
        # mid-word. They live here now, where they can wrap.
        note = ttk.Frame(f, style="Panel.TFrame", padding=(12, 8))
        note.pack(fill="x", padx=6, pady=(0, 8))
        self.lbl_farm_note_h = ttk.Label(note, text="Select an island",
                                         style="H2.TLabel", background=PANEL)
        self.lbl_farm_note_h.pack(anchor="w")
        self.lbl_farm_note = ttk.Label(note, text="", style="Dim.TLabel",
                                       background=PANEL, wraplength=1500,
                                       justify="left")
        self.lbl_farm_note.pack(anchor="w", pady=(2, 0))

    # ---------------- tab: zone ----------------

    def _on_farm_select(self, _evt=None):
        sel = self.tv_farm.selection()
        if not sel:
            return
        iid = sel[0]
        parent = self.tv_farm.parent(iid)
        head = self.tv_farm.item(parent or iid, "text").strip()
        isl = None
        for i in self.tracker.data["islands"]:
            label = "%s  %s" % (i["id"], i["name"])
            if head.startswith(label):
                isl = i
                break
        if isl is None and head.startswith("EFREETI"):
            isl = self.tracker.island_by_id("EFREETI")
        if isl is None:
            self.lbl_farm_note_h.configure(text=head)
            self.lbl_farm_note.configure(text="")
            return
        title = "%s  %s" % (isl["id"], isl["name"])
        if isl.get("boss"):
            title += "   —   %s" % isl["boss"]
        if isl.get("needs_key"):
            title += "      (needs %s)" % isl["needs_key"]
        self.lbl_farm_note_h.configure(text=title)
        self.lbl_farm_note.configure(text=isl.get("notes", "") or "No special mechanics noted.")

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

    # ---------------- tab: epics ----------------

    def _build_epics(self):
        f = self.tab_epics

        self.frm_epic_warn = ttk.Frame(f, style="Warn.TFrame", padding=(12, 8))
        self.frm_epic_warn.pack(fill="x", padx=4, pady=(8, 4))
        self.lbl_epic_warn_h = ttk.Label(self.frm_epic_warn, text="",
                                         style="WarnHead.TLabel")
        self.lbl_epic_warn_h.pack(anchor="w")
        self.lbl_epic_warn_lead = ttk.Label(self.frm_epic_warn, text="", wraplength=1500,
                                            justify="left", style="WarnBody.TLabel")
        self.lbl_epic_warn_lead.pack(anchor="w", pady=(2, 0))

        self.var_warn_open = tk.BooleanVar(value=False)
        self.btn_warn = ttk.Button(self.frm_epic_warn, text="Why?  ▾", width=12,
                                   command=self._toggle_epic_warn)
        self.btn_warn.pack(anchor="w", pady=(6, 0))
        self.lbl_epic_warn_b = ttk.Label(self.frm_epic_warn, text="", wraplength=1500,
                                         justify="left", style="WarnBody.TLabel")

        bar = ttk.Frame(f, padding=(4, 2))
        bar.pack(fill="x")
        self.var_only_now = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text="Show only steps whose zone is live now",
                        variable=self.var_only_now, style="Ck.TCheckbutton",
                        command=self._on_epic_select).pack(side="left")
        ttk.Label(bar, text="   Double-click a step to mark the item as held.",
                  style="Dim.TLabel").pack(side="left")

        left = ttk.Frame(f, padding=(4, 6))
        left.pack(side="left", fill="both", expand=True)
        cols = ("reward", "now", "blocked")
        self.tv_epic = ttk.Treeview(left, columns=cols, show="tree headings")
        self.tv_epic.heading("#0", text="Class")
        self.tv_epic.heading("reward", text="Epic reward")
        self.tv_epic.heading("now", text="Zone live")
        self.tv_epic.heading("blocked", text="Not reachable")
        self.tv_epic.column("#0", width=120, anchor="w")
        self.tv_epic.column("reward", width=230, anchor="w")
        self.tv_epic.column("now", width=120, anchor="center")
        self.tv_epic.column("blocked", width=80, anchor="center")
        self.tv_epic.pack(fill="both", expand=True)
        self.tv_epic.bind("<<TreeviewSelect>>", self._on_epic_select)
        _stripe(self.tv_epic)
        self.tv_epic.tag_configure("allheld", foreground=OK)

        right = ttk.Frame(f, style="Panel.TFrame", padding=12, width=470)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)
        self.lbl_epic_head = ttk.Label(right, text="Select a class",
                                       style="H2.TLabel", background=PANEL)
        self.lbl_epic_head.pack(anchor="w")
        self.lbl_epic_sum = ttk.Label(right, text="", style="Dim.TLabel",
                                      background=PANEL, wraplength=430,
                                      justify="left")
        self.lbl_epic_sum.pack(anchor="w", pady=(0, 8))
        self.txt_epic = tk.Text(right, wrap="word", bg=PANEL, fg=FG, bd=0,
                                font=("Segoe UI", 9), padx=2, pady=2,
                                highlightthickness=0)
        self.txt_epic.pack(fill="both", expand=True)
        self.txt_epic.tag_configure("h", font=("Segoe UI Semibold", 10),
                                    foreground=ACCENT, spacing1=8, spacing3=3)
        self.txt_epic.tag_configure("held", foreground=OK)
        self.txt_epic.tag_configure("now", foreground=FG)
        self.txt_epic.tag_configure("blocked", foreground=DIM)
        self.txt_epic.tag_configure("dim", foreground=DIM)
        self.txt_epic.bind("<Double-1>", self._toggle_epic_have)
        self.txt_epic.configure(state="disabled")

    def _toggle_epic_warn(self):
        opening = not self.var_warn_open.get()
        self.var_warn_open.set(opening)
        if opening:
            self.lbl_epic_warn_b.pack(anchor="w", pady=(6, 0))
            self.btn_warn.configure(text="Hide  ▴")
        else:
            self.lbl_epic_warn_b.pack_forget()
            self.btn_warn.configure(text="Why?  ▾")

    def _fill_epics(self):
        if not self.epics:
            return
        et = self.epics
        s = et.summary()
        comp = s.get("completable") or []
        allzones = s.get("zones_all_live") or []
        if et.epics_released:
            self.lbl_epic_warn_h.configure(
                text="Epics are live" + (" - Kunark too" if et.kunark_released else ""))
            body = et.availability_note()
        else:
            self.lbl_epic_warn_h.configure(
                text="No epic is completable yet — epics are Patch 18, after Kunark "
                     "(Patch 13). Era, not zone, is the gate.")
            self.lbl_epic_warn_lead.configure(
                text="%d of %d steps sit in zones you can already reach: route planning "
                     "only, not a shopping list — the epic items and NPCs do not exist yet."
                     % (s["zone_live"], s["steps_total"]))
            parts = [et.availability_note()]
            if allzones:
                parts.append("Every zone in the %s chains is already live, so those are the "
                             "first that become doable when the Epics era lands."
                             % " and ".join(allzones))
            parts += ["", et.exception_note(), "", et.data_warning()]
            body = "\n".join(parts)
        self.lbl_epic_warn_b.configure(text=body)

        tv = self.tv_epic
        keep = self._selected_epic_class()
        tv.delete(*tv.get_children())
        target = None
        for r in et.class_rows():
            outstanding = r["now"] - r["held_now"]
            tag = ("allheld",) if r["now"] and outstanding == 0 else ()
            iid = tv.insert("", "end", text="  " + r["name"], tags=tag, values=(
                r["reward"],
                "%d / %d held" % (r["held_now"], r["now"]) if r["now"] else "none",
                r["blocked"] or ""))
            if r["name"] == keep:
                target = iid
        kids = tv.get_children()
        if target:
            tv.selection_set(target)
        elif kids:
            tv.selection_set(kids[0])

    def _selected_epic_class(self):
        sel = self.tv_epic.selection()
        if not sel:
            return None
        return self.tv_epic.item(sel[0], "text").strip()

    def _on_epic_select(self, _evt=None):
        name = self._selected_epic_class()
        if not name or not self.epics:
            return
        rec = self.epics.by_name(name)
        if not rec:
            return
        rows = self.epics.steps_for(name, only_now=self.var_only_now.get())
        held = sum(1 for r in rows if r["held"])
        self.lbl_epic_head.configure(text="%s  -  %s" % (name, rec["reward"]))
        self.lbl_epic_sum.configure(
            text="%s\n%d of %d shown steps held."
                 % (rec.get("summary", ""), held, len(rows)))

        t = self.txt_epic
        t.configure(state="normal")
        t.delete("1.0", "end")
        if not rows:
            t.insert("end", "Nothing in this chain is collectable yet.\n", "dim")
        cur = None
        for r in rows:
            if r["era"] != cur:
                cur = r["era"]
                t.insert("end", "%s\n" % self.epics.data["eras"][cur]["label"], "h")
            mark = "[x]" if r["held"] else "[ ]"
            tag = "held" if r["held"] else ("blocked" if r["blocked"] else "now")
            t.insert("end", "  %s %s  %s\n" % (mark, r["step"], r["item"]), tag)
            src = r["mob"] or "?"
            if r["zone"]:
                src += "  -  " + r["zone"]
            t.insert("end", "        %s\n" % src, "dim")
            if r["held"] and r["where"]:
                t.insert("end", "        held in %s\n" % r["where"], "held")
            if r["notes"]:
                t.insert("end", "        %s\n" % r["notes"], "dim")
        t.configure(state="disabled")

    def _toggle_epic_have(self, event):
        """Double-click a line in the epic detail pane to toggle 'I have this'."""
        if not self.epics:
            return
        idx = self.txt_epic.index("@%d,%d linestart" % (event.x, event.y))
        line = self.txt_epic.get(idx, "%s lineend" % idx).strip()
        item = None
        for prefix in ("[x] ", "[ ] "):
            if line.startswith(prefix):
                rest = line[len(prefix):]
                parts = rest.split(None, 1)
                item = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                break
        if not item:
            return
        key = "epic_have:" + item
        if self.overrides.pop(key, None) is None:
            self.overrides[key] = True
        model.save_overrides(self.overrides)
        self.reload()

    # ---------------- tab: search ----------------

    def _build_search(self):
        f = self.tab_search
        head = ttk.Frame(f, padding=(6, 10))
        head.pack(fill="x")
        ttk.Label(head, text="Search everything", style="H2.TLabel").pack(anchor="w")
        ttk.Label(head, style="Dim.TLabel", justify="left", text=(
            "The Plane of Sky Tests and all 15 epic chains at once — item, mob, zone, "
            "class or Test name.    Ctrl+F focuses, Esc clears.")
        ).pack(anchor="w", pady=(2, 8))

        row = ttk.Frame(head)
        row.pack(fill="x")
        self.var_query = tk.StringVar()
        self.ent_search = ttk.Entry(row, textvariable=self.var_query,
                                    font=("Segoe UI", 12))
        self.ent_search.pack(side="left", fill="x", expand=True, ipady=3)
        self.ent_search.bind("<KeyRelease>", self._do_search)
        self.ent_search.bind("<Escape>", lambda _e: (self.var_query.set(""),
                                                     self._do_search()))
        ttk.Button(row, text="Clear",
                   command=lambda: (self.var_query.set(""), self._do_search())
                   ).pack(side="left", padx=6)

        chips = ttk.Frame(head)
        chips.pack(fill="x", pady=(8, 0))
        ttk.Label(chips, text="Jump to:", style="Dim.TLabel").pack(side="left", padx=(0, 6))
        for label in ("Plane of Hate", "Plane of Fear", "Plane of Sky", "Gorgalosk",
                      "Spiroc Lord", "Bazzt Zzzt", "Sister of the Spire",
                      "Eye of Veeshan", "Efreeti"):
            ttk.Button(chips, text=label, width=len(label) + 2,
                       command=lambda q=label: self._search_for(q)).pack(side="left", padx=2)

        opts = ttk.Frame(head)
        opts.pack(fill="x", pady=(6, 0))
        self.var_hide_held = tk.BooleanVar(value=False)
        self.var_hide_blocked = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Hide what I already hold",
                        variable=self.var_hide_held, style="Ck.TCheckbutton",
                        command=self._do_search).pack(side="left")
        ttk.Checkbutton(opts, text="Hide Kunark-blocked",
                        variable=self.var_hide_blocked, style="Ck.TCheckbutton",
                        command=self._do_search).pack(side="left", padx=14)
        self.lbl_hits = ttk.Label(opts, text="", style="Dim.TLabel")
        self.lbl_hits.pack(side="right")

        cols = ("item", "source", "zone", "cls", "context", "status")
        self.tv_search = ttk.Treeview(f, columns=cols, show="headings")
        for c, t, w in (("item", "Item", 210), ("source", "From", 165),
                        ("zone", "Zone / island", 190), ("cls", "Class", 100),
                        ("context", "For", 230), ("status", "Status", 110)):
            self.tv_search.heading(c, text=t)
            self.tv_search.column(c, width=w, anchor="w")
        self.tv_search.pack(fill="both", expand=True, padx=6, pady=(6, 8))
        _stripe(self.tv_search)
        self.tv_search.tag_configure("held", foreground=OK)
        self.tv_search.tag_configure("blocked", foreground=DIM)
        self.tv_search.tag_configure("done", foreground=DIM)
        self.tv_search.bind("<Double-1>", self._jump_from_search)

    def _search_for(self, query):
        self.nb.select(self.tab_search)
        self.var_query.set(query)
        self._do_search()

    def _focus_search(self, _evt=None):
        self.nb.select(self.tab_search)
        self.ent_search.focus_set()
        self.ent_search.select_range(0, "end")
        return "break"

    def _do_search(self, _evt=None):
        tv = self.tv_search
        tv.delete(*tv.get_children())
        q = self.var_query.get().strip()
        if not q:
            self._fill_most_wanted()
            return
        hits = model.search(self.index, q)
        shown = 0
        for r in hits:
            if self.var_hide_held.get() and r["held"]:
                continue
            if self.var_hide_blocked.get() and r["blocked"]:
                continue
            if r["done"]:
                status, tag = "done", "done"
            elif r["held"]:
                status, tag = "held: " + (r["where"] or "yes"), "held"
            elif r["blocked"]:
                status, tag = "needs Kunark", "blocked"
            else:
                status, tag = "not held", ""
            tv.insert("", "end", tags=(tag,) if tag else (), values=(
                r["item"], r["mob"], r["zone"], "%s %s" % (r["dataset"], r["cls"]),
                r["context"], status))
            shown += 1
        _restripe(tv)
        extra = "" if shown == len(hits) else " (%d hidden by filters)" % (len(hits) - shown)
        self.lbl_hits.configure(text="%d result%s%s"
                                     % (shown, "" if shown == 1 else "s", extra))

    def _fill_most_wanted(self):
        """With no query, show what the most Tests are waiting on."""
        tv = self.tv_search
        rows = []
        for iid, items in self.tracker.farm_list().items():
            isl = self.tracker.island_by_id(iid)
            zone = "%s %s" % (isl.get("id", ""), isl.get("name", ""))
            for it in items:
                rows.append((it["count"], it["item"], it["source"], zone.strip(),
                             "; ".join("%s %s" % (c, t) for c, t in it["needed_by"])))
        rows.sort(key=lambda r: (-r[0], r[1]))
        for n, item, mob, zone, users in rows[:18]:
            tv.insert("", "end", values=(
                item, mob, zone, "Sky", users,
                "wanted by %d" % n if n > 1 else "not held"))
        _restripe(tv)
        self.lbl_hits.configure(
            text="Most-wanted — start typing to search everything")

    def _jump_from_search(self, _evt=None):
        """Double-click a result to open its class in the relevant tab."""
        sel = self.tv_search.selection()
        if not sel:
            return
        vals = self.tv_search.item(sel[0], "values")
        if len(vals) < 4:
            return
        dataset, _, cls = vals[3].partition(" ")
        if dataset == model.EPIC and self.epics:
            self.nb.select(self.tab_epics)
            for iid in self.tv_epic.get_children():
                if self.tv_epic.item(iid, "text").strip() == cls:
                    self.tv_epic.selection_set(iid)
                    self.tv_epic.see(iid)
                    break
        else:
            self.nb.select(self.tab_classes)
            for iid in self.tv_class.get_children():
                if self.tv_class.item(iid, "text").strip() == cls:
                    self.tv_class.selection_set(iid)
                    self.tv_class.see(iid)
                    break

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

        if self.epic_data:
            self.epics = model.EpicTracker(self.epic_data, inv, self.overrides)

        self.index = model.build_index(self.tracker, self.epics)
        if hasattr(self, "tv_search"):
            self._do_search()

        self._fill_classes()
        self._fill_ready()
        self._fill_farm()
        self._fill_zone()
        if self.epics:
            self._fill_epics()
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
        sky = self.tracker.summary()
        ready_rows = [r for r in self.tracker.all_progress() if r["ready"]]
        ready_total = sum(r["ready"] for r in ready_rows)

        bits = [("Character", who or "-", False)]
        if ach.get("race_created"):
            bits.append(("Race", ach["race_created"], False))
        primary = [c for c, r in ach["classes"].items() if r.get("confirmed_primary")]
        if primary:
            bits.append(("Primary", primary[0], False))
        bits.append(("Classes", "%d/%d" % (sky["classes_unlocked"], sky["classes_total"]), False))
        bits.append(("To farm", str(sky["items_to_farm"]), False))
        bits.append(("Ready", str(ready_total), ready_total > 0))

        for w in self.stats.winfo_children():
            w.destroy()
        for i, (k, v, hot) in enumerate(bits):
            if i:
                ttk.Label(self.stats, text="│", style="StatK.TLabel").pack(
                    side="left", padx=12)
            cell = ttk.Frame(self.stats)
            cell.pack(side="left")
            ttk.Label(cell, text=k.upper(), style="StatK.TLabel").pack(anchor="w")
            ttk.Label(cell, text=v,
                      style="StatVa.TLabel" if hot else "StatV.TLabel").pack(anchor="w")

        if ready_total:
            names = ", ".join("%s (%d)" % (r["name"], r["ready"]) for r in ready_rows[:4])
            self.lbl_next.configure(
                text="▶  %d Test%s ready to turn in now — %s"
                     % (ready_total, "" if ready_total == 1 else "s", names))
            self.frm_next.pack(fill="x", padx=16, pady=(8, 0),
                               before=self.nb)
        else:
            closest = next((r for r in self.tracker.all_progress()
                            if not r["unlocked"]), None)
            if closest:
                self.lbl_next.configure(
                    text="▶  Closest to unlocking: %s — %d Test%s left"
                         % (closest["name"], closest["remaining"],
                            "" if closest["remaining"] == 1 else "s"))
            else:
                self.lbl_next.configure(text="▶  All classes unlocked.")

    def _fill_classes(self):
        tv = self.tv_class
        sel = tv.selection()
        keep = tv.item(sel[0], "text").strip() if sel else None
        tv.delete(*tv.get_children())
        for r in self.tracker.all_progress():
            # one cell per Test - a 5/6 and a 6/7 must not look identical
            bar = "▰" * r["done"] + "▱" * (r["total"] - r["done"])
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
                "" if r["unlocked"] else r["remaining"],
                "%s  %d/%d" % (bar, r["done"], r["total"]),
                status, r["npc"]))
        _restripe(tv)
        kids = tv.get_children()
        target = None
        if keep:
            target = next((k for k in kids if tv.item(k, "text").strip() == keep), None)
        if target:
            tv.selection_set(target)
            tv.see(target)
        elif kids:
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
                               values=("%d items" % len(items), ""), open=True)
            for it in items:
                users = "; ".join("%s %s" % (c, t) for c, t in it["needed_by"])
                tv.insert(parent, "end", text="      " + it["item"],
                          tags=("multi",) if it["count"] > 1 else (),
                          values=("×%d" % it["count"] if it["count"] > 1 else "",
                                  users))
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
        stem = "Epics" if which == "epics" else "PlaneOfSky"
        default = stem + "_%s_%s.pdf" % (
            self.paths.get("character") or "character",
            datetime.date.today().isoformat())
        path = filedialog.asksaveasfilename(
            title="Save PDF", defaultextension=".pdf", initialfile=default,
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            if which == "epics":
                pdfout.export_epics(self.epics, path)
            else:
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
        opts = [("classes", "Sky: class unlock progress + outstanding Tests"),
                ("farm", "Sky: farming list, grouped by boss"),
                ("all", "Sky: both (full report)")]
        if getattr(parent, "epics", None):
            opts.append(("epics", "Epics: what you can collect now"))
        for key, label in opts:
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
