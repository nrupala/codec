import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext, font as tkfont

from codec.config import Config
from codec.engine import CodeCEngine


class CodeCDesktop:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CodeC - AI Coding Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg="#0d1117")

        self.engine: CodeCEngine | None = None
        self.loop = asyncio.new_event_loop()
        self._init_engine()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_engine(self):
        def _init():
            self.loop.run_until_complete(self._async_init())
        threading.Thread(target=_init, daemon=True).start()

    async def _async_init(self):
        config = Config()
        self.engine = CodeCEngine(config)

    def _build_ui(self):
        font_family = "Consolas"
        try:
            tkfont.Font(family="Cascadia Code", size=12)
            font_family = "Cascadia Code"
        except tk.TclError:
            try:
                tkfont.Font(family="Fira Code", size=12)
                font_family = "Fira Code"
            except tk.TclError:
                pass

        chat_font = tkfont.Font(family=font_family, size=11)

        header = tk.Frame(self.root, bg="#161b22", height=40)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        title = tk.Label(header, text="CodeC v0.2.0", fg="#58a6ff",
                         bg="#161b22", font=tkfont.Font(family=font_family, size=12, weight="bold"))
        title.pack(side=tk.LEFT, padx=12, pady=8)

        status = tk.Label(header, text="● Connected", fg="#3fb950",
                          bg="#161b22", font=tkfont.Font(family=font_family, size=10))
        status.pack(side=tk.RIGHT, padx=12, pady=8)

        body_frame = tk.Frame(self.root, bg="#0d1117")
        body_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        self.output = scrolledtext.ScrolledText(
            body_frame, bg="#0d1117", fg="#c9d1d9",
            font=chat_font, wrap=tk.WORD, state=tk.DISABLED,
            borderwidth=0, highlightthickness=0,
            padx=12, pady=8,
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        self.output.tag_config("system", foreground="#8b949e", font=tkfont.Font(family=font_family, size=10, slant="italic"))
        self.output.tag_config("user", foreground="#e6edf3")
        self.output.tag_config("assistant", foreground="#c9d1d9")
        self.output.tag_config("error", foreground="#f85149")
        self.output.tag_config("code", foreground="#ffa657")

        input_frame = tk.Frame(self.root, bg="#161b22", height=50)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        input_frame.pack_propagate(False)

        prompt = tk.Label(input_frame, text="$", fg="#3fb950",
                          bg="#161b22", font=tkfont.Font(family=font_family, size=13, weight="bold"))
        prompt.pack(side=tk.LEFT, padx=(12, 4), pady=12)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            input_frame, textvariable=self.input_var, bg="#0d1117", fg="#c9d1d9",
            font=chat_font, borderwidth=0, highlightthickness=0,
            insertbackground="#c9d1d9",
        )
        self.input_entry.pack(fill=tk.X, expand=True, padx=(0, 8), pady=10)
        self.input_entry.bind("<Return>", self._on_send)

        send_btn = tk.Button(
            input_frame, text="Send", bg="#238636", fg="white",
            activebackground="#2ea043", activeforeground="white",
            borderwidth=0, padx=12, pady=4, cursor="hand2",
            font=tkfont.Font(family=font_family, size=10),
            command=self._on_send,
        )
        send_btn.pack(side=tk.RIGHT, padx=(0, 12), pady=10)

        self._append("system", "CodeC v0.2.0 — AI coding assistant. Type /help for commands.")

    def _append(self, role: str, text: str):
        self.output.config(state=tk.NORMAL)
        tag = role if role in ("system", "user", "assistant", "error", "code") else "assistant"
        prefix = {"user": "┃ ", "assistant": "", "system": "◆ ", "error": "✗ "}.get(role, "")
        self.output.insert(tk.END, f"{prefix}{text}\n\n", tag)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _on_send(self, event=None):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self._append("user", text)
        self.input_entry.config(state=tk.DISABLED)
        threading.Thread(target=self._process_message, args=(text,), daemon=True).start()

    def _process_message(self, text: str):
        if not self.engine:
            self.root.after(0, lambda: self._append("error", "Engine not ready. Please wait..."))
            self.root.after(0, lambda: self.input_entry.config(state=tk.NORMAL))
            return

        async def run():
            return await self.engine.process(text)

        try:
            result = self.loop.run_until_complete(run())
            self.root.after(0, lambda: self._append("assistant", result))
        except SystemExit:
            self.root.after(0, self._on_close)
        except Exception as e:
            self.root.after(0, lambda: self._append("error", str(e)))
        finally:
            self.root.after(0, lambda: self.input_entry.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.input_entry.focus())

    def _on_close(self):
        if self.engine:
            async def cleanup():
                await self.engine.cleanup()
            self.loop.run_until_complete(cleanup())
        self.loop.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def run():
    app = CodeCDesktop()
    app.run()


if __name__ == "__main__":
    run()
