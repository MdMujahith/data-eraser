"""ARIVIM-style Textual CSS theme."""

from __future__ import annotations

APP_CSS = """
Screen {
    background: #0a0a0f;
    color: #00e5ff;
}

/* ── Header ──────────────────────────────────────────────────── */
#header {
    height: auto;
    background: #0a0a0f;
    border: solid #00bcd4;
    padding: 0 2;
    margin: 0 1;
}
#welcome-line {
    content-align: center middle;
    color: #546e7a;
    height: 1;
}
#ascii-title {
    content-align: center middle;
    color: #00e5ff;
    text-style: bold;
    height: auto;
}
#version-badge {
    content-align: right middle;
    color: #00e676;
    text-style: bold;
    height: 1;
    padding: 0 2;
}
#subtitle-line {
    content-align: center middle;
    color: #546e7a;
    height: 1;
    border-top: dashed #1a3a4a;
    padding: 0 2;
}

/* ── Status bar ──────────────────────────────────────────────── */
#status-bar {
    height: 1;
    background: #050510;
    padding: 0 2;
    border-bottom: solid #00bcd4;
    border-top: solid #00bcd4;
}

/* ── Body ────────────────────────────────────────────────────── */
#body {
    layout: horizontal;
    height: 1fr;
    margin: 0 1;
}

/* ── Panels ──────────────────────────────────────────────────── */
#menu-panel {
    border: solid #00bcd4;
    background: #0a0a0f;
    padding: 1 2;
    width: 58%;
}
#overview-panel {
    border: solid #00bcd4;
    background: #0a0a0f;
    padding: 1 2;
    width: 42%;
    margin-left: 1;
}
.panel-title {
    color: #00e5ff;
    text-style: bold;
    content-align: center middle;
    height: 1;
    margin-bottom: 1;
}

/* ── Menu items ──────────────────────────────────────────────── */
.menu-row {
    height: 1;
    layout: horizontal;
}
.menu-row:hover { background: #0d1f2d; }
.m-key   { color: #00bcd4; text-style: bold; width: 6; }
.m-label { color: #e0f7fa; width: 22; }
.m-desc  { color: #37474f; }

/* ── Overview stats ──────────────────────────────────────────── */
.ov-row   { height: 1; layout: horizontal; }
.ov-label { color: #546e7a; width: 18; }
.ov-val   { color: #00e676; text-style: bold; }
.ov-val-w { color: #ffab40; text-style: bold; }
.ov-val-e { color: #ff5252; text-style: bold; }

/* ── Quick links ─────────────────────────────────────────────── */
#quick-links {
    height: 3;
    background: #050510;
    border: solid #00bcd4;
    margin: 0 1;
    padding: 0 3;
    content-align: left middle;
}

/* ── Shortcut bar ────────────────────────────────────────────── */
#shortcut-bar {
    height: 1;
    background: #050510;
    padding: 0 2;
    border-top: solid #1a3a4a;
    content-align: left middle;
}

/* ── Command input ───────────────────────────────────────────── */
#cmd-bar {
    height: 3;
    background: #0a0a0f;
    border: solid #00bcd4;
    margin: 0 1;
    layout: horizontal;
    padding: 0 1;
}
#cmd-prompt {
    color: #00bcd4;
    text-style: bold;
    width: 4;
    content-align: center middle;
}
#cmd-input {
    background: #0a0a0f;
    color: #00e5ff;
    border: none;
    width: 1fr;
}
#cmd-input:focus { background: #0d1f2d; border: none; }

/* ── Log ─────────────────────────────────────────────────────── */
#log-area {
    height: 6;
    border: solid #1a3a4a;
    background: #05050f;
    margin: 0 1;
    padding: 0 1;
}

/* ── Screen titles ───────────────────────────────────────────── */
.screen-title {
    height: 3;
    content-align: center middle;
    color: #00bcd4;
    text-style: bold;
    border-bottom: solid #00bcd4;
    background: #050510;
}
.back-hint {
    height: 1;
    color: #37474f;
    padding: 0 2;
}

/* ── DataTable ───────────────────────────────────────────────── */
DataTable {
    background: #0a0a0f;
    color: #00e5ff;
    border: solid #1a3a4a;
    margin: 0 1;
}
DataTable > .datatable--header {
    background: #050510;
    color: #00bcd4;
    text-style: bold;
}
DataTable > .datatable--cursor { background: #0d2137; color: #ffffff; }

/* ── Buttons ─────────────────────────────────────────────────── */
Button { background: #0d1f2d; color: #00e5ff; border: solid #00bcd4; margin: 0 1; }
Button:hover { background: #1a3a5c; }
Button.-primary { background: #004d5c; border: solid #00e5ff; }

/* ── Scrollbar ───────────────────────────────────────────────── */
ScrollBar { background: #0a0a0f; }
ScrollBar > .scrollbar--bar { background: #00bcd4; }

Footer { background: #050510; color: #37474f; }
"""
