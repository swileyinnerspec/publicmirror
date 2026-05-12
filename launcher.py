import os
import subprocess
import shlex
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from Xlib import display, X

# optional onboard
try:
    import subprocess as sp
    ONBOARD_OK = True
except Exception:
    ONBOARD_OK = False


# ---------------- X11 ----------------

xdisp = display.Display()
root_x = xdisp.screen().root


def get_focused_window():
    try:
        prop = root_x.get_full_property(
            xdisp.intern_atom("_NET_ACTIVE_WINDOW"),
            X.AnyPropertyType
        )
        if prop:
            return xdisp.create_resource_object("window", prop.value[0])
    except Exception:
        pass
    return None


def focus_launcher(win):
    try:
        win.raise_window()
        win.set_input_focus(X.RevertToParent, X.CurrentTime)
        xdisp.sync()
    except Exception:
        pass


# ---------------- desktop apps ----------------

ICON_SIZE = (48, 48)


def launch(cmd):
    try:
        subprocess.Popen(shlex.split(cmd))
    except Exception:
        pass


def parse_desktop(path):
    name = exe = icon = None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Name=") and not name:
                    name = line.split("=", 1)[1]
                elif line.startswith("Exec=") and not exe:
                    exe = line.split("=", 1)[1]
                elif line.startswith("Icon=") and not icon:
                    icon = line.split("=", 1)[1]
    except Exception:
        return None

    if not name or not exe:
        return None

    exe = exe.split("%")[0].strip()
    return name, exe, icon


def load_apps():
    apps = []
    for d in ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".desktop"):
                p = parse_desktop(os.path.join(d, f))
                if p:
                    apps.append(p)
    return sorted(apps, key=lambda x: x[0].lower())


# ---------------- notifications ----------------

notifications = []


# ---------------- UI base ----------------

class ScrollArea(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.inner = tk.Frame(self.canvas)

        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))

        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


# ---------------- Launcher ----------------

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()

        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.attributes("-fullscreen", True)
        self.overrideredirect(True)

        self.bind("<Escape>", lambda e: self.destroy())

        self.tabs = tk.Frame(self, bg="#222")
        self.tabs.pack(fill="x")

        self.area = ScrollArea(self)
        self.area.pack(fill="both", expand=True)

        # ALWAYS include Notifications tab
        self.tab_list = ["Apps", "Windows", "Notifications"]

        for t in self.tab_list:
            tk.Button(
                self.tabs,
                text=t,
                command=lambda tt=t: self.switch(tt),
                bg="#333",
                fg="white",
                relief="flat"
            ).pack(side="left")

        self.icon_cache = {}
        self.switch("Apps")

    def clear(self):
        for w in self.area.inner.winfo_children():
            w.destroy()

    def switch(self, tab):
        self.clear()
        if tab == "Apps":
            self.show_apps()
        elif tab == "Windows":
            self.show_windows()
        elif tab == "Notifications":
            self.show_notifications()

    # ---------------- apps ----------------

    def show_apps(self):
        apps = load_apps()

        cols = 6
        r = c = 0

        for name, exe, icon in apps:
            tk.Button(
                self.area.inner,
                text=name,
                compound="top",
                width=20,
                height=4,
                command=lambda e=exe: launch(e)
            ).grid(row=r, column=c, padx=4, pady=4)

            c += 1
            if c >= cols:
                c = 0
                r += 1

    # ---------------- windows ----------------

    def show_windows(self):
        wins = []

        try:
            for w in root_x.query_tree().children:
                try:
                    n = w.get_wm_name()
                    if n:
                        wins.append((n, w))
                except Exception:
                    pass
        except Exception:
            pass

        for name, win in wins:
            row = tk.Frame(self.area.inner)
            row.pack(fill="x")

            tk.Label(row, text=name).pack(side="left", fill="x", expand=True)

            tk.Button(
                row,
                text="Focus",
                command=lambda ww=win: focus_launcher(ww)
            ).pack(side="right")

    # ---------------- notifications ----------------

    def show_notifications(self):
        for ts, msg in notifications:
            tk.Label(
                self.area.inner,
                text=f"[{ts}] {msg}",
                anchor="w",
                justify="left"
            ).pack(fill="x")


# ---------------- Dock (BOTTOM PANEL) ----------------

class Dock(tk.Toplevel):
    def __init__(self):
        super().__init__()

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        height = 50

        self.geometry(f"{sw}x{height}+0+{sh - height}")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # STRUT: ask WM to reserve space (works on many X11 WMs)
        try:
            self._set_strut(height)
        except Exception:
            pass

        tk.Button(self, text="Focus Launcher", command=self.focus_launcher).pack(side="left")
        tk.Button(self, text="Toggle Onboard", command=self.toggle_onboard).pack(side="left")

        self.onboard_proc = None

    def _set_strut(self, h):
        self.update_idletasks()
        self.wm_property = self.winfo_id()

        # reserve bottom panel space
        self._change_property = self.tk.call(
            "wm",
            "attributes",
            self,
            "-type",
            "dock"
        )

    def focus_launcher(self):
        # simply raise launcher instead of minimizing anything
        try:
            for w in self.master.winfo_children():
                w.lift()
        except Exception:
            pass

    def toggle_onboard(self):
        if not ONBOARD_OK:
            return

        if self.onboard_proc:
            try:
                self.onboard_proc.terminate()
            except Exception:
                pass
            self.onboard_proc = None
        else:
            try:
                self.onboard_proc = subprocess.Popen(["onboard"])
            except Exception:
                self.onboard_proc = None


# ---------------- MAIN ----------------

if __name__ == "__main__":
    Launcher()
    Dock()
    tk.mainloop()