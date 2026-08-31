"""PDF export via reportlab. Three report types, all printable on Letter."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak)

from . import model

BLACK = colors.black
GREY = colors.HexColor("#eeeeee")
MIDGREY = colors.HexColor("#888888")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1x", parent=ss["Title"], fontSize=16, spaceAfter=2,
                          alignment=0, textColor=BLACK))
    ss.add(ParagraphStyle("Sub", parent=ss["Normal"], fontSize=8,
                          textColor=colors.HexColor("#333333"), spaceAfter=8))
    ss.add(ParagraphStyle("H2x", parent=ss["Heading2"], fontSize=11, spaceBefore=10,
                          spaceAfter=4, textColor=BLACK))
    ss.add(ParagraphStyle("Cell", parent=ss["Normal"], fontSize=8, leading=9.6))
    ss.add(ParagraphStyle("CellB", parent=ss["Normal"], fontSize=8, leading=9.6,
                          fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle("Note", parent=ss["Normal"], fontSize=7.2, leading=8.8,
                          textColor=colors.HexColor("#333333")))
    return ss


def _table(rows, widths, header=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), GREY),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.9, BLACK)]
    t.setStyle(TableStyle(style))
    return t


def _footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 6.8)
    canv.setFillColor(MIDGREY)
    canv.drawString(14 * mm, 10 * mm,
                    "Refresh with:  %s   and   %s" % model.COMMANDS)
    canv.drawRightString(letter[0] - 14 * mm, 10 * mm, "Page %d" % doc.page)
    canv.restoreState()


def _header(story, ss, tracker, title):
    z = tracker.data["zone"]
    s = tracker.summary()
    ach = tracker.ach
    who = []
    if ach.get("race_created"):
        who.append(ach["race_created"])
    primary = [c for c, r in ach["classes"].items() if r.get("confirmed_primary")]
    if primary:
        who.append("Primary: " + primary[0])
    story.append(Paragraph(title, ss["H1x"]))
    story.append(Paragraph(
        "%s &middot; %s &nbsp;|&nbsp; Classes unlocked <b>%d/%d</b> &nbsp;|&nbsp; "
        "Tests done <b>%d/%d</b> &nbsp;|&nbsp; Items to farm <b>%d</b>%s"
        % (z["name"], tracker.data["game"], s["classes_unlocked"], s["classes_total"],
           s["done"], s["tests_total"], s["items_to_farm"],
           ("  &nbsp;|&nbsp; " + " &middot; ".join(who)) if who else ""),
        ss["Sub"]))


def export(tracker, path, kind="all"):
    ss = _styles()
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=12 * mm, bottomMargin=16 * mm,
                            title="EQL Plane of Sky Tracker")
    story = []
    titles = {"classes": "Plane of Sky - Class Unlock Progress",
              "farm": "Plane of Sky - Farming List",
              "all": "Plane of Sky - Tracker Report"}
    _header(story, ss, tracker, titles.get(kind, titles["all"]))

    if kind in ("classes", "all"):
        _classes_section(story, ss, tracker)
    if kind == "all":
        story.append(PageBreak())
    if kind in ("farm", "all"):
        _farm_section(story, ss, tracker)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return path


def _classes_section(story, ss, tracker):
    story.append(Paragraph("Class unlock progress", ss["H2x"]))
    story.append(Paragraph(
        "Sorted by how close each class is to unlocking. Completing a class's Sky Tests "
        "unlocks it as a Primary Class option in loadouts.", ss["Note"]))
    story.append(Spacer(1, 3))

    rows = [[Paragraph(h, ss["CellB"]) for h in
             ("Class", "Progress", "Left", "Turn-in NPC", "Status")]]
    for r in tracker.all_progress():
        bar = "#" * r["done"] + "." * (r["total"] - r["done"])
        status = ("UNLOCKED" + (" (token)" if r["token_used"] and not r["confirmed_primary"] else "")
                  if r["unlocked"] else
                  ("%d ready to turn in" % r["ready"] if r["ready"] else ""))
        if r["confirmed_primary"]:
            status = "PRIMARY CLASS"
        rows.append([Paragraph(r["name"], ss["CellB"] if not r["unlocked"] else ss["Cell"]),
                     Paragraph("%s  %d/%d" % (bar, r["done"], r["total"]), ss["Cell"]),
                     Paragraph("" if r["unlocked"] else str(r["remaining"]), ss["Cell"]),
                     Paragraph(r["npc"], ss["Cell"]),
                     Paragraph(status, ss["Cell"])])
    story.append(_table(rows, [30 * mm, 42 * mm, 12 * mm, 42 * mm, 40 * mm]))

    story.append(Paragraph("Outstanding Tests by class", ss["H2x"]))
    for cls in tracker.data["classes"]:
        pending = []
        for t in cls["tests"]:
            st, have, need = tracker.test_status(cls, t)
            if st == model.DONE:
                continue
            pending.append((t, st, have, need))
        if not pending:
            continue
        story.append(Spacer(1, 4))
        story.append(Paragraph("%s &nbsp;&mdash;&nbsp; turn in to %s"
                               % (cls["name"], cls["turnin_npc"]), ss["CellB"]))
        rows = [[Paragraph(h, ss["CellB"]) for h in
                 ("Test", "Wind Rune", "Still need", "From", "Reward")]]
        for t, st, have, need in pending:
            if st == model.READY:
                needtxt, fromtxt = "<b>ready - components held</b>", ""
            else:
                needtxt = "<br/>".join(c["item"] for c in need)
                fromtxt = "<br/>".join(c["source"] for c in need)
            rows.append([Paragraph(t["test"], ss["Cell"]),
                         Paragraph(t["rune"].replace("Wind Rune ", ""), ss["Cell"]),
                         Paragraph(needtxt, ss["Cell"]),
                         Paragraph(fromtxt, ss["Cell"]),
                         Paragraph(t["reward"], ss["Cell"])])
        story.append(_table(rows, [34 * mm, 16 * mm, 40 * mm, 36 * mm, 40 * mm]))


def _farm_section(story, ss, tracker):
    story.append(Paragraph("Farming list - what to kill, and what it gives you", ss["H2x"]))
    story.append(Paragraph(
        "Turn-ins CONSUME the component, so an item needed by two Tests must be farmed twice "
        "- shown as x2 below.", ss["Note"]))
    for iid, items in tracker.farm_list().items():
        isl = tracker.island_by_id(iid)
        story.append(Spacer(1, 5))
        head = "%s &nbsp;&middot;&nbsp; %s" % (isl["id"], isl["name"])
        if isl.get("boss"):
            head += " &nbsp;&middot;&nbsp; %s" % isl["boss"]
        head += " &nbsp;&mdash;&nbsp; %d item%s" % (len(items), "" if len(items) == 1 else "s")
        story.append(Paragraph(head, ss["CellB"]))
        if isl.get("needs_key"):
            story.append(Paragraph("Requires: %s" % isl["needs_key"], ss["Note"]))
        rows = [[Paragraph(h, ss["CellB"]) for h in ("", "Item", "Needed by")]]
        for it in items:
            label = it["item"] + ("  x%d" % it["count"] if it["count"] > 1 else "")
            users = "<br/>".join("%s - %s" % (c, t) for c, t in it["needed_by"])
            rows.append([Paragraph("[ ]", ss["Cell"]),
                         Paragraph(label, ss["CellB"] if it["count"] > 1 else ss["Cell"]),
                         Paragraph(users, ss["Cell"])])
        story.append(_table(rows, [8 * mm, 62 * mm, 96 * mm]))
        if isl.get("notes"):
            story.append(Paragraph(isl["notes"], ss["Note"]))
