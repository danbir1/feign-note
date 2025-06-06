import tkinter as tk
from tkinter import filedialog, simpledialog, colorchooser
from PIL import Image, ImageTk
import os

class FeignTrackerApp:
    def __init__(self, root):
        self.root = root
        root.title("Feign 추리노트")

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        ctrl = tk.Frame(root)
        ctrl.pack(fill=tk.X, pady=4)
        tk.Button(ctrl, text="📂 스크린샷 불러오기", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="🎨 수동 색상 선택", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        self.mode_btn = tk.Button(ctrl, text="🔲 자동 픽셀 색상", command=self.toggle_mode)
        self.mode_btn.pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="📝 메모 토글", command=self.toggle_memo).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="❌ 현재 라운드 삭제", command=self.clear_current_round).pack(side=tk.LEFT, padx=5)
        tk.Button(ctrl, text="🔄 전체 초기화", command=self.reset_all).pack(side=tk.LEFT, padx=5)

        round_frame = tk.Frame(root)
        round_frame.pack(fill=tk.X, pady=4)
        self.round_buttons = []
        for i in range(1, 11):
            btn = tk.Button(round_frame, text=f"{i}R", command=lambda r=i: self.switch_round(r))
            btn.pack(side=tk.LEFT, padx=2)
            self.round_buttons.append(btn)

        self.memo_win = None
        self.memo_texts = {i: "" for i in range(1, 11)}
        self.memo_widget = None

        self.orig_img = None
        self.disp_img = None
        self.tk_img = None
        self.scale_x = self.scale_y = 1
        self.manual_mode = False
        self.current_color = "#000000"
        self.start_xy = None
        self.preview_line = None
        self.round_lines = {i: [] for i in range(1, 11)}
        self.current_round = 1
        self.role_labels = {}

        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.canvas.bind("<Button-3>", self.on_right_click)
        root.bind("<Control-z>", self.on_undo)

        self.role_icons = {}
        icon_dir = os.path.join(os.path.dirname(__file__), "feign_icon")
        if os.path.exists(icon_dir):
            for fname in os.listdir(icon_dir):
                if fname.endswith(".png"):
                    role_name = os.path.splitext(fname)[0]
                    img_path = os.path.join(icon_dir, fname)
                    icon_img = Image.open(img_path).resize((25, 25), Image.LANCZOS)
                    self.role_icons[role_name] = ImageTk.PhotoImage(icon_img)

        self.highlight_round_button(1)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("이미지", "*.png;*.jpg;*.jpeg")])
        if not path:
            return
        self.orig_img = Image.open(path)
        img = self.orig_img.copy()
        img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        self.disp_img = img
        self.tk_img = ImageTk.PhotoImage(img)

        self.scale_x = self.orig_img.width / img.width
        self.scale_y = self.orig_img.height / img.height

        self.canvas.config(width=img.width, height=img.height)
        self.redraw_all()

    def choose_color(self):
        c = colorchooser.askcolor(title="선 색상 선택")[1]
        if c:
            self.current_color = c
            self.manual_mode = True
            self.mode_btn.config(text="🔲 수동 색상")

    def toggle_mode(self):
        self.manual_mode = not self.manual_mode
        self.mode_btn.config(text="🔲 수동 색상" if self.manual_mode else "🔲 자동 픽셀 색상")

    def on_down(self, e):
        if not self.disp_img:
            return
        x, y = e.x, e.y
        if not self.manual_mode:
            ox = int(x * self.scale_x)
            oy = int(y * self.scale_y)
            if 0 <= ox < self.orig_img.width and 0 <= oy < self.orig_img.height:
                pix = self.orig_img.getpixel((ox, oy))
                if isinstance(pix, tuple):
                    pix = pix[:3]
                r, g, b = pix
                self.current_color = f"#{r:02x}{g:02x}{b:02x}"
        self.start_xy = (x, y)

    def on_drag(self, e):
        if not self.start_xy:
            return
        if self.preview_line:
            self.canvas.delete(self.preview_line)
        x0, y0 = self.start_xy
        self.preview_line = self.canvas.create_line(x0, y0, e.x, e.y, fill=self.current_color, width=2, dash=(4, 2))

    def on_up(self, e):
        if not self.start_xy:
            return
        if self.preview_line:
            self.canvas.delete(self.preview_line)
            self.preview_line = None
        x0, y0 = self.start_xy
        x1, y1 = e.x, e.y
        self.canvas.create_line(x0, y0, x1, y1, fill=self.current_color, width=3)
        self.round_lines[self.current_round].append((x0, y0, x1, y1, self.current_color))
        self.start_xy = None

    def on_undo(self, e=None):
        if self.round_lines[self.current_round]:
            self.round_lines[self.current_round].pop()
            self.redraw_all()

    def on_right_click(self, e):
        key = (e.x // 10, e.y // 10)

        def open_text_input():
            role = simpledialog.askstring("직업 입력", "직업을 입력하세요:")
            if not role:
                return
            self.role_labels[key] = {"type": "text", "value": role, "color": "#FFFFFF"}
            self.redraw_all()

        def open_icon_picker():
            if hasattr(self, "icon_win") and self.icon_win and tk.Toplevel.winfo_exists(self.icon_win):
                self.icon_win.destroy()

            self.icon_win = tk.Toplevel(self.root)
            self.icon_win.title("직업 아이콘 선택")
            self.icon_win.geometry("+%d+%d" % (self.root.winfo_pointerx(), self.root.winfo_pointery()))

            for idx, (name, icon_img) in enumerate(self.role_icons.items()):
                btn = tk.Button(self.icon_win, image=icon_img, command=lambda n=name: select_icon(n))
                btn.grid(row=idx // 6, column=idx % 6, padx=3, pady=3)

        def select_icon(role_name):
            self.role_labels[key] = {"type": "image", "value": role_name}
            self.redraw_all()
            self.icon_win.destroy()

        def choose_entry_type():
            picker = tk.Toplevel(self.root)
            picker.title("입력 방식 선택")
            tk.Button(picker, text="텍스트 입력", command=lambda: [picker.destroy(), open_text_input()]).pack(pady=5)
            tk.Button(picker, text="아이콘 선택", command=lambda: [picker.destroy(), open_icon_picker()]).pack(pady=5)

        if e.state & 0x0001:
            if key in self.role_labels:
                del self.role_labels[key]
                self.redraw_all()
        else:
            choose_entry_type()

    def toggle_memo(self):
        if self.memo_win and tk.Toplevel.winfo_exists(self.memo_win):
            self.memo_texts[self.current_round] = self.memo_widget.get("1.0", tk.END)
            self.memo_win.destroy()
            self.memo_win = None
            return

        self.memo_win = tk.Toplevel(self.root)
        self.memo_win.title("📝 추리 메모")

        btn_frame = tk.Frame(self.memo_win)
        btn_frame.pack(fill=tk.X)
        for i in range(1, 11):
            tk.Button(btn_frame, text=f"{i}R", command=lambda r=i: self.switch_memo_round(r)).pack(side=tk.LEFT, padx=1)

        self.memo_widget = tk.Text(self.memo_win, width=45, height=20, font=("마른 고딕", 10))
        self.memo_widget.pack(fill=tk.BOTH, expand=True)
        self.memo_widget.insert("1.0", self.memo_texts[self.current_round])

        tk.Button(self.memo_win, text="전체삭제", command=lambda: self.memo_widget.delete("1.0", tk.END)).pack(pady=2)

    def switch_memo_round(self, r):
        if self.memo_widget:
            self.memo_texts[self.current_round] = self.memo_widget.get("1.0", tk.END)
            self.current_round = r
            self.memo_widget.delete("1.0", tk.END)
            self.memo_widget.insert("1.0", self.memo_texts[self.current_round])
            self.highlight_round_button(r)
            self.redraw_all()

    def switch_round(self, r):
        self.current_round = r
        self.highlight_round_button(r)
        self.redraw_all()

    def highlight_round_button(self, r):
        for i, btn in enumerate(self.round_buttons, start=1):
            btn.config(relief=tk.SUNKEN if i == r else tk.RAISED)

    def redraw_all(self):
        self.canvas.delete("all")
        if self.tk_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        for (gx, gy), data in self.role_labels.items():
            x = gx * 10 + 5
            y = gy * 10 + 5
            if data["type"] == "text":
                self.canvas.create_text(x, y, text=data["value"], fill="#FFFFFF", font=("Arial", 10, "bold"))
            elif data["type"] == "image":
                img = self.role_icons.get(data["value"])
                if img:
                    self.canvas.create_image(x, y, image=img)

        for x0, y0, x1, y1, color in self.round_lines[self.current_round]:
            self.canvas.create_line(x0, y0, x1, y1, fill=color, width=3)

    def clear_current_round(self):
        self.round_lines[self.current_round] = []
        self.redraw_all()

    def reset_all(self):
        self.orig_img = None
        self.tk_img = None
        self.disp_img = None
        self.canvas.delete("all")
        self.role_labels.clear()
        self.round_lines = {i: [] for i in range(1, 11)}
        self.memo_texts = {i: "" for i in range(1, 11)}
        self.current_round = 1
        self.highlight_round_button(1)
        if self.memo_win and tk.Toplevel.winfo_exists(self.memo_win):
            self.memo_win.destroy()
            self.memo_win = None

if __name__ == "__main__":
    root = tk.Tk()
    FeignTrackerApp(root)
    root.mainloop()
