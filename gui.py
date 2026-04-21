import os
import random
import threading
import tkinter as tk
from tkinter import scrolledtext

import requests

from conversation import ConversationManager
from ollama_client import chat
from prompt_builder import (
    build_chat_messages,
    build_expression_messages,
    build_feedback_messages,
    build_opening_messages,
)
from voice import speak, start_recording, stop_recording

# ── 定数 ──────────────────────────────────────────
OLLAMA_URL  = "http://localhost:11434"
MAX_TURNS   = 3
WINDOW_SIZE = "700x620"

LOG_COLORS = {
    "You":      "#1a3c6b",
    "AI":       "#1a6b3c",
    "System":   "#888888",
    "Feedback": "#8b4513",
    "表現提案":  "#6b3a1a",
}


def _load_topics() -> list:
    base_path  = os.path.dirname(os.path.abspath(__file__))
    topics_path = os.path.join(base_path, "topics.txt")
    with open(topics_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root   = root
        self.root.title("English Conversation Practice")
        self.root.geometry(WINDOW_SIZE)
        self.conv   = ConversationManager()
        self.topics = _load_topics()
        self.topic  = random.choice(self.topics)
        self._check_ollama()
        self._build_ui()
        self._show_topic_selection()

    # ── Ollama確認 ────────────────────────────────
    def _check_ollama(self) -> None:
        try:
            requests.get(OLLAMA_URL, timeout=2)
        except Exception:
            import tkinter.messagebox as mb
            mb.showerror(
                "Ollamaが起動していません",
                "OllamaをインストールしてからPCを再起動してください。\nhttps://ollama.com"
            )
            self.root.quit()

    # ── UI構築 ────────────────────────────────────
    def _build_ui(self) -> None:
        self.topic_label = tk.Label(
            self.root, text="",
            font=("Arial", 13, "bold"), fg="#1a6b3c", wraplength=660
        )
        self.topic_label.pack(pady=(16, 4))

        self.turn_label = tk.Label(
            self.root, text=f"Turn: 0 / {MAX_TURNS}",
            font=("Arial", 10), fg="#888"
        )
        self.turn_label.pack()

        self.log = scrolledtext.ScrolledText(
            self.root, state="disabled",
            font=("Arial", 11), wrap=tk.WORD, height=22
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.X, padx=16, pady=(0, 4))

        self.entry = tk.Entry(frame, font=("Arial", 12), state="disabled")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", lambda _: self._send())

        self.send_btn = tk.Button(
            frame, text="Send", command=self._send,
            font=("Arial", 12), bg="#1a6b3c", fg="white", state="disabled"
        )
        self.send_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.mic_btn = tk.Button(
            frame, text="🎤",
            font=("Arial", 14), bg="#1a3c6b", fg="white",
            width=3, state="disabled"
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.mic_btn.bind("<ButtonPress-1>",   self._on_mic_press)
        self.mic_btn.bind("<ButtonRelease-1>", self._on_mic_release)

        self.mic_status = tk.Label(
            self.root, text="",
            font=("Arial", 10), fg="#e05000"
        )
        self.mic_status.pack()

    # ── 入力制御 ──────────────────────────────────
    def _enable_input(self) -> None:
        self.entry.config(state="normal")
        self.send_btn.config(state="normal")
        self.mic_btn.config(state="normal")
        self.mic_status.config(text="▶ 話しかけてください")

    def _disable_input(self) -> None:
        self.entry.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.mic_btn.config(state="disabled")

    # ── ログ表示 ──────────────────────────────────
    def _append_log(self, role: str, text: str) -> None:
        self.log.config(state="normal")
        color = LOG_COLORS.get(role, "#000")
        tag   = f"role_{role}"
        self.log.insert(tk.END, f"\n{role}:\n", tag)
        self.log.insert(tk.END, f"{text}\n")
        self.log.tag_config(tag, foreground=color, font=("Arial", 11, "bold"))
        self.log.config(state="disabled")
        self.log.see(tk.END)

    def _update_turn_label(self) -> None:
        self.turn_label.config(
            text=f"Turn: {self.conv.turn_count} / {MAX_TURNS}"
        )

    # ── トピック選択 ──────────────────────────────
    def _show_topic_selection(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Today's Topic")
        win.geometry("460x280")
        win.grab_set()
        win.resizable(False, False)

        tk.Label(
            win, text="今日のトピックを選んでください",
            font=("Arial", 12, "bold")
        ).pack(pady=(20, 12))

        candidates   = random.sample(self.topics, min(3, len(self.topics)))
        selected_var = tk.StringVar(value=candidates[0])
        self.topic   = candidates[0]

        radio_frame = tk.Frame(win)
        radio_frame.pack(fill=tk.X, padx=40)

        def _render(topics: list) -> None:
            for w in radio_frame.winfo_children():
                w.destroy()
            self.topic = topics[0]
            selected_var.set(topics[0])
            for t in topics:
                tk.Radiobutton(
                    radio_frame, text=t,
                    variable=selected_var, value=t,
                    command=lambda t=t: setattr(self, "topic", t),
                    font=("Arial", 11), wraplength=380, justify="left"
                ).pack(anchor="w", pady=4)

        _render(candidates)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(16, 0))

        tk.Button(
            btn_frame, text="このトピックで始める", width=18,
            command=lambda: [win.destroy(), self._start_conversation()],
            font=("Arial", 11), bg="#1a6b3c", fg="white"
        ).pack(side=tk.LEFT, padx=8)

        tk.Button(
            btn_frame, text="別の3候補", width=12,
            command=lambda: _render(
                random.sample(self.topics, min(3, len(self.topics)))
            ),
            font=("Arial", 11)
        ).pack(side=tk.LEFT, padx=8)

    def _start_conversation(self) -> None:
        self.topic_label.config(text=f"🎯 Today's Topic: {self.topic}")
        self._append_log("System", f"Topic: {self.topic}")
        self._ai_opening()

    # ── AIオープニング ────────────────────────────
    def _ai_opening(self) -> None:
        self._append_log("System", "AIが会話を始めます...")

        def _generate() -> None:
            try:
                opening = chat(build_opening_messages(self.topic))
                self.conv.add("assistant", opening)
                self.root.after(0, lambda: self._on_ai_opening(opening))
            except Exception as e:
                import traceback
                print(f"opening error: {e}")
                traceback.print_exc()
                self.root.after(0, self._enable_input)

        threading.Thread(target=_generate, daemon=True).start()

    def _on_ai_opening(self, opening: str) -> None:
        self._append_log("AI", opening)
        speak(opening)
        self._enable_input()

    # ── 送信 ──────────────────────────────────────
    def _send(self) -> None:
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self.entry.delete(0, tk.END)
        self._disable_input()
        self._append_log("You", user_input)
        self.conv.add("user", user_input)
        self._update_turn_label()

        if self.conv.is_feedback_time():
            self._show_feedback()
            return

        def _generate() -> None:
            try:
                reply = chat(build_chat_messages(self.conv.get_history()))
                self.conv.add("assistant", reply)
                self.root.after(0, lambda: self._on_reply(reply))
            except Exception as e:
                import traceback
                print(f"generate error: {e}")
                traceback.print_exc()
                self.root.after(0, self._enable_input)

        threading.Thread(target=_generate, daemon=True).start()

    def _on_reply(self, reply: str) -> None:
        self._append_log("AI", reply)
        speak(reply)
        self._enable_input()

    # ── マイク ────────────────────────────────────
    def _on_mic_press(self, _event) -> None:
        self._disable_input()
        self.mic_btn.config(bg="#e05000", state="normal")
        self.mic_status.config(text="🔴 録音中...")
        start_recording()

    def _on_mic_release(self, _event) -> None:
        self.mic_btn.config(bg="#1a3c6b")
        self.mic_status.config(text="⏳ 認識中...")

        def _transcribe() -> None:
            text = stop_recording()
            self.root.after(0, lambda: self._on_recorded(text))

        threading.Thread(target=_transcribe, daemon=True).start()

    def _on_recorded(self, text: str) -> None:
        if text:
            self.entry.config(state="normal")
            self.entry.delete(0, tk.END)
            self.entry.insert(0, text)
            self.mic_status.config(text="")
            self._send()
        else:
            self._enable_input()
            self.mic_status.config(text="⚠️ 認識できませんでした")

    # ── フィードバック ────────────────────────────
    def _show_feedback(self) -> None:
        self._append_log("System", "--- 3 turns completed! Generating feedback... ---")

        def _generate() -> None:
            try:
                feedback = chat(build_feedback_messages(self.conv.get_history()))
                self.root.after(0, lambda: self._on_feedback(feedback))
            except Exception as e:
                import traceback
                print(f"feedback error: {e}")
                traceback.print_exc()

        threading.Thread(target=_generate, daemon=True).start()

    def _on_feedback(self, feedback: str) -> None:
        self._append_log("Feedback", feedback)
        self._show_expression_area()

        win = tk.Toplevel(self.root)
        win.title("Continue?")
        win.geometry("300x120")
        tk.Label(win, text="続けますか？", font=("Arial", 13)).pack(pady=16)
        btn_frame = tk.Frame(win)
        btn_frame.pack()
        tk.Button(
            btn_frame, text="続ける", width=10,
            command=lambda: [self._reset_session(), win.destroy()],
            font=("Arial", 11)
        ).pack(side=tk.LEFT, padx=8)
        tk.Button(
            btn_frame, text="終了", width=10,
            command=self.root.quit,
            font=("Arial", 11)
        ).pack(side=tk.LEFT, padx=8)

    # ── 表現提案 ──────────────────────────────────
    def _show_expression_area(self) -> None:
        if hasattr(self, "expression_frame"):
            self.expression_frame.destroy()

        self.expression_frame = tk.Frame(self.root, bg="#f5f0e8")
        self.expression_frame.pack(fill=tk.X, padx=16, pady=(0, 8))

        tk.Label(
            self.expression_frame,
            text="💬 言いたかった日本語を入力すると英語表現を提案します",
            font=("Arial", 11, "bold"), bg="#f5f0e8"
        ).pack(anchor="w", pady=(8, 4))

        tk.Label(
            self.expression_frame,
            text="例：「昨日映画を見に行ったんだけど、すごく面白かった」",
            font=("Arial", 10), bg="#f5f0e8", fg="#555"
        ).pack(anchor="w")

        input_frame = tk.Frame(self.expression_frame, bg="#f5f0e8")
        input_frame.pack(fill=tk.X, pady=4)

        self.intention_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.intention_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.intention_entry.bind("<Return>", lambda _: self._get_expression())

        tk.Button(
            input_frame, text="提案を見る",
            command=self._get_expression,
            font=("Arial", 10), bg="#6b3a1a", fg="white"
        ).pack(side=tk.LEFT, padx=(8, 0))

    def _get_expression(self) -> None:
        intention = self.intention_entry.get().strip()
        if not intention:
            return
        self.intention_entry.config(state="disabled")
        self._append_log("System", f"「{intention}」の自然な表現を生成中...")

        def _generate() -> None:
            try:
                result = chat(build_expression_messages(
                    intention, self.conv.get_history()
                ))
                self.root.after(0, lambda: self._on_expression(result))
            except Exception as e:
                import traceback
                print(f"expression error: {e}")
                traceback.print_exc()
                self.root.after(
                    0, lambda: self.intention_entry.config(state="normal")
                )

        threading.Thread(target=_generate, daemon=True).start()

    def _on_expression(self, result: str) -> None:
        self._append_log("表現提案", result)
        self.intention_entry.config(state="normal")
        self.intention_entry.delete(0, tk.END)

    # ── リセット ──────────────────────────────────
    def _reset_session(self) -> None:
        self.conv.reset()
        self._disable_input()
        self.topic = random.choice(self.topics)
        if hasattr(self, "expression_frame"):
            self.expression_frame.destroy()
        self.turn_label.config(text=f"Turn: 0 / {MAX_TURNS}")
        self._show_topic_selection()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
