import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font
import os
import threading
import asyncio
from epub_processor import translate_epub_async
from google import genai
import logging


class TextHandler(logging.Handler):
    """Custom logging handler to display logs in a Tkinter Text widget."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Thread-safe GUI update
        self.text_widget.after(0, self.text_widget.insert, tk.END, msg + "\n")


class TranslatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.font=tkinter.font.Font(family="Malgun Gothic", size=20)

        self.title("Sea Marine EPUB Translator")
        self.geometry("700x650")
        self.input_path = None
        self.output_path = None

        # API Key 입력
        self.api_key_label = tk.Label(self, text="API Key:", font=self.font)
        self.api_key_label.pack(pady=5)
        self.api_key_entry = tk.Entry(self, width=50, show="*")
        self.api_key_entry.pack(pady=5)

        # Gemini 모델 선택 (Combobox)
        self.gemini_model_label = tk.Label(self, text="Gemini Model:", font=self.font)
        self.gemini_model_label.pack(pady=5)
        self.gemini_model_combobox = ttk.Combobox(
            self,
            values=[
                "Gemini 2.5 Pro Experimental",
                "Gemini 2.0 Flash",
                "Gemini 1.5 Pro"
            ],
            state="readonly",
            width=40
        )
        self.gemini_model_combobox.set("Gemini 2.0 Flash")
        self.gemini_model_combobox.pack(pady=5)

        # 청크 사이즈 입력
        self.chunk_size_label = tk.Label(self, text="Chunk Size (문자수):", font=self.font)
        self.chunk_size_label.pack(pady=5)
        self.chunk_size_spinbox = tk.Spinbox(self, from_=1000, to=10000, width=10)
        self.chunk_size_spinbox.delete(0, tk.END)
        self.chunk_size_spinbox.insert(0, "3000")
        self.chunk_size_spinbox.pack(pady=5)

        # 유저 커스텀 프롬프트 입력
        self.custom_prompt_label = tk.Label(self, text="Custom Prompt (비워두면 기본값 사용):", font=self.font)
        self.custom_prompt_label.pack(pady=5)
        self.custom_prompt_text = tk.Text(self, height=6, width=60)
        self.custom_prompt_text.pack(pady=5)

        # 최대 동시 요청 수 설정
        self.concurrent_label = tk.Label(self, text="Max Concurrent Requests (1-10):", font=self.font)
        self.concurrent_label.pack(pady=5)
        self.concurrent_spinbox = tk.Spinbox(self, from_=1, to=20, width=5)
        self.concurrent_spinbox.delete(0, tk.END)
        self.concurrent_spinbox.insert(0, "1")
        self.concurrent_spinbox.pack(pady=5)

        # EPUB 파일 선택 버튼
        self.select_button = tk.Button(self, text="Select Epub File", command=self.select_file)
        self.select_button.pack(pady=10)
        self.file_label = tk.Label(self, text="Selected File: None", font=self.font)
        self.file_label.pack()

        # 번역 시작 버튼
        self.translate_button = tk.Button(self, text="Start Translation", command=self.start_translation, state=tk.DISABLED)
        self.translate_button.pack(pady=10)

        # 진행 상황 표시용 텍스트 박스
        self.log_text = tk.Text(self, height=10)
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 진행바 - 0~100%
        self.progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", maximum=100)
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        self.progress['value'] = 0

        # 로깅 설정 (GUI에 로그 출력)
        self.setup_logging()

    def setup_logging(self):
        """Sets up logging to display in the GUI text widget."""
        self.logger = logging.getLogger("TranslatorGUI")
        self.logger.setLevel(logging.INFO)
        text_handler = TextHandler(self.log_text)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        text_handler.setFormatter(formatter)
        self.logger.addHandler(text_handler)
        # Root logger에도 핸들러 추가 (다른 모듈의 로그도 포함)
        logging.getLogger().addHandler(text_handler)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("EPUB Files", "*.epub"), ("All Files", "*.*")]
        )
        if file_path:
            self.input_path = file_path
            self.file_label.config(text=f"Selected File: {os.path.basename(file_path)}")
            self.translate_button.config(state=tk.NORMAL)

    def update_progress(self, percentage):
        """
        Update the progress bar.
         - 첫 번째 LLM 응답: 10%
         - 마지막 LLM 응답: 90%
         - 파일 완성: 100%
        """
        self.progress['value'] = percentage
        self.progress.update_idletasks()
        self.logger.info(f"Progress updated: {percentage}%")

    def start_translation(self):
        if not self.input_path:
            messagebox.showwarning("WARNING", "Please select an EPUB file first!")
            return
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            messagebox.showwarning("WARNING", "Please enter your API key!")
            return
        try:
            max_concurrent = int(self.concurrent_spinbox.get())
            if max_concurrent < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("WARNING", "Invalid concurrent requests value.")
            return

        # Gemini 모델 선택 및 API용 모델명으로 변환
        gemini_model_display = self.gemini_model_combobox.get().strip()
        model_mapping = {
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        gemini_model = model_mapping.get(gemini_model_display, "gemini-2.0-flash")

        # 청크 사이즈와 커스텀 프롬프트
        try:
            chunk_size = int(self.chunk_size_spinbox.get())
        except ValueError:
            messagebox.showwarning("WARNING", "Invalid chunk size value.")
            return
        custom_prompt = self.custom_prompt_text.get("1.0", tk.END).strip()
        if not custom_prompt:
            custom_prompt = None  # 기본 프롬프트 사용

        dir_name = os.path.dirname(self.input_path)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(dir_name, base_name + "_translated.epub")

        # 번역 중 버튼 비활성화
        self.translate_button.config(state=tk.DISABLED)
        self.select_button.config(state=tk.DISABLED)
        self.log_text.insert(tk.END, "Starting translation...\n")
        self.update_progress(0)

        # 별도 스레드에서 번역 실행
        threading.Thread(
            target=self.run_translation,
            args=(max_concurrent, gemini_model, chunk_size, custom_prompt),
            daemon=True
        ).start()

    def run_translation(self, max_concurrent, gemini_model, chunk_size, custom_prompt):
        try:
            api_key = self.api_key_entry.get().strip()
            global client
            client = genai.Client(api_key=api_key)
            import translator_core
            translator_core.set_client(client)
            # 모델, 청크 사이즈, 커스텀 프롬프트 설정
            translator_core.set_llm_model(gemini_model)
            translator_core.set_chunk_size(chunk_size)
            translator_core.set_custom_prompt(custom_prompt)
            asyncio.run(translate_epub_async(
                self.input_path,
                self.output_path,
                max_concurrent,
                progress_callback=self.update_progress
            ))
            self.log_text.insert(tk.END, f"Translation completed! File: {self.output_path}\n")
            self.update_progress(100)
        except Exception as e:
            self.log_text.insert(tk.END, f"An error occurred during translation: {e}\n")
            self.logger.error(f"Translation error: {e}")
        finally:
            self.translate_button.config(state=tk.NORMAL)
            self.select_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    app = TranslatorGUI()
    app.mainloop()
