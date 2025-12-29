import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import csv
import subprocess
import threading
import time
from pathlib import Path
import tempfile
import sys

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class ZSParserApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("ZS Parser")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # App state
        self.current_data = None
        self.current_temp_file = None
        self.current_filename = None
        self.current_format = "csv"

        self.setup_ui()

    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))

        header_title = ctk.CTkLabel(
            self.header_frame,
            text="ZS Parser",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        header_title.pack(pady=10)

        header_subtitle = ctk.CTkLabel(
            self.header_frame,
            text="Drag and drop NDJSON files to parse",
            font=ctk.CTkFont(size=14)
        )
        header_subtitle.pack(pady=(0, 10))

        # Format selection
        self.format_frame = ctk.CTkFrame(self.main_frame)
        self.format_frame.pack(fill="x", padx=20, pady=10)

        format_title = ctk.CTkLabel(
            self.format_frame,
            text="Output Format",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        format_title.pack(pady=(15, 5))

        format_options_frame = ctk.CTkFrame(self.format_frame)
        format_options_frame.pack(pady=(0, 15))

        self.format_var = tk.StringVar(value="csv")

        csv_radio = ctk.CTkRadioButton(
            format_options_frame,
            text="CSV - Comma-separated values",
            variable=self.format_var,
            value="csv",
            command=self.on_format_change
        )
        csv_radio.pack(pady=5, padx=20, anchor="w")

        json_radio = ctk.CTkRadioButton(
            format_options_frame,
            text="JSON - JavaScript Object Notation",
            variable=self.format_var,
            value="json",
            command=self.on_format_change
        )
        json_radio.pack(pady=5, padx=20, anchor="w")

        # File drop zone
        self.drop_frame = ctk.CTkFrame(self.main_frame, height=200)
        self.drop_frame.pack(fill="x", padx=20, pady=10)
        self.drop_frame.pack_propagate(False)

        # Drop zone content
        drop_icon = ctk.CTkLabel(
            self.drop_frame,
            text="📁",
            font=ctk.CTkFont(size=48)
        )
        drop_icon.pack(pady=(30, 10))

        drop_title = ctk.CTkLabel(
            self.drop_frame,
            text="Drop files here",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        drop_title.pack(pady=5)

        drop_subtitle = ctk.CTkLabel(
            self.drop_frame,
            text="Supports .ndjson, .json formats"
        )
        drop_subtitle.pack(pady=5)

        self.browse_btn = ctk.CTkButton(
            self.drop_frame,
            text="Browse Files",
            command=self.browse_files,
            width=120,
            height=32
        )
        self.browse_btn.pack(pady=15)

        # Setup drag and drop
        self.setup_drag_drop()

        # Status section
        self.status_frame = ctk.CTkFrame(self.main_frame)

        status_title = ctk.CTkLabel(
            self.status_frame,
            text="Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.pack(pady=(15, 10))

        # Status items
        status_content = ctk.CTkFrame(self.status_frame)
        status_content.pack(fill="x", padx=20, pady=(0, 15))

        self.file_label = ctk.CTkLabel(status_content, text="File: -")
        self.file_label.pack(anchor="w", pady=2)

        self.status_label = ctk.CTkLabel(status_content, text="Status: Waiting")
        self.status_label.pack(anchor="w", pady=2)

        self.records_label = ctk.CTkLabel(status_content, text="Records: -")
        self.records_label.pack(anchor="w", pady=2)

        # Logs section
        self.logs_frame = ctk.CTkFrame(self.main_frame)

        logs_title = ctk.CTkLabel(
            self.logs_frame,
            text="Parsing Logs",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        logs_title.pack(pady=(15, 10))

        self.logs_textbox = ctk.CTkTextbox(
            self.logs_frame,
            height=100,
            wrap="word"
        )
        self.logs_textbox.pack(fill="x", padx=20, pady=(0, 15))

        # Results section
        self.results_frame = ctk.CTkFrame(self.main_frame)

        # Results header with actions
        results_header = ctk.CTkFrame(self.results_frame)
        results_header.pack(fill="x", padx=20, pady=(15, 10))

        results_title = ctk.CTkLabel(
            results_header,
            text="Parsing Results",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        results_title.pack(side="left")

        actions_frame = ctk.CTkFrame(results_header)
        actions_frame.pack(side="right")

        self.save_btn = ctk.CTkButton(
            actions_frame,
            text="💾 Save File",
            command=self.save_file,
            width=100
        )
        self.save_btn.pack(side="left", padx=5)

        self.copy_btn = ctk.CTkButton(
            actions_frame,
            text="📋 Copy Data",
            command=self.copy_to_clipboard,
            width=100
        )
        self.copy_btn.pack(side="left", padx=5)

        # Results summary
        self.results_summary = ctk.CTkLabel(
            self.results_frame,
            text="Ready to export...",
            font=ctk.CTkFont(size=14)
        )
        self.results_summary.pack(pady=10)

        # Results preview
        preview_title = ctk.CTkLabel(
            self.results_frame,
            text="Data Preview (First 3 Records)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        preview_title.pack(anchor="w", padx=20, pady=(10, 5))

        self.preview_textbox = ctk.CTkTextbox(
            self.results_frame,
            height=200,
            wrap="word"
        )
        self.preview_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Hide sections initially
        self.hide_section(self.status_frame)
        self.hide_section(self.logs_frame)
        self.hide_section(self.results_frame)

    def setup_drag_drop(self):
        # Enable drag and drop for the drop frame
        def on_drop(event):
            files = self.root.tk.splitlist(event.data)
            if files:
                self.process_file(files[0])

        def on_drag_enter(event):
            self.drop_frame.configure(fg_color=("#3B8ED0", "#1F6AA5"))
            return event.action

        def on_drag_leave(event):
            self.drop_frame.configure(fg_color=("gray90", "gray13"))

        # Configure drag and drop
        self.drop_frame.drop_target_register('DND_Files')
        self.drop_frame.dnd_bind('<<Drop>>', on_drop)
        self.drop_frame.dnd_bind('<<DragEnter>>', on_drag_enter)
        self.drop_frame.dnd_bind('<<DragLeave>>', on_drag_leave)

    def on_format_change(self):
        self.current_format = self.format_var.get()

    def browse_files(self):
        file_path = filedialog.askopenfilename(
            title="Select file to parse",
            filetypes=[
                ("JSON files", "*.json *.ndjson"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        if not self.is_valid_file(file_path):
            messagebox.showerror("Error", "Please select .ndjson or .json files")
            return

        # Clean up previous temp file
        if self.current_temp_file:
            self.cleanup_temp_file()

        self.current_filename = os.path.basename(file_path)
        self.update_status("processing", self.current_filename, "Parsing...")
        self.show_section(self.status_frame)
        self.hide_section(self.logs_frame)
        self.hide_section(self.results_frame)

        # Run parsing in a separate thread
        thread = threading.Thread(target=self.parse_file_thread, args=(file_path,))
        thread.daemon = True
        thread.start()

    def parse_file_thread(self, file_path):
        try:
            # Generate output path
            input_filename = Path(file_path).stem
            timestamp = int(time.time() * 1000)
            file_extension = "csv" if self.current_format == "csv" else "json"
            output_filename = f"{input_filename}_parsed_{timestamp}.{file_extension}"
            output_path = os.path.join(os.getcwd(), output_filename)

            # Run Python parser
            script_path = os.path.join("src", "zs_parser", "main.py")
            process = subprocess.Popen(
                ["python3", script_path, file_path, "--output", output_path, "--format", self.current_format],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate()

            # Update UI in main thread
            self.root.after(0, self.handle_parse_result, process.returncode, output_path, stderr, stdout)

        except Exception as e:
            self.root.after(0, self.handle_parse_error, str(e))

    def handle_parse_result(self, return_code, output_path, stderr, stdout):
        if return_code == 0:
            try:
                # Read the generated output file
                if self.current_format == "csv":
                    with open(output_path, 'r', encoding='utf-8') as f:
                        self.current_data = f.read()
                else:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        self.current_data = json.load(f)

                self.current_temp_file = output_path

                # Calculate record count
                if self.current_format == "csv":
                    record_count = len(self.current_data.split('\n')) - 2  # -2 for header and empty line
                else:
                    record_count = len(self.current_data) if isinstance(self.current_data, list) else 1

                self.update_status("success", self.current_filename, "Parsing completed", record_count)
                self.show_logs(stderr)
                self.show_results(self.current_data)

            except Exception as e:
                self.handle_parse_error(f"Failed to read output: {str(e)}")
        else:
            self.update_status("error", self.current_filename, "Parsing failed")
            self.show_logs(stderr)
            messagebox.showerror("Error", f"Parser failed with code {return_code}")

    def handle_parse_error(self, error_message):
        self.update_status("error", self.current_filename or "Unknown", "Parsing failed")
        messagebox.showerror("Error", error_message)

    def is_valid_file(self, file_path):
        valid_extensions = ['.json', '.ndjson']
        return any(file_path.lower().endswith(ext) for ext in valid_extensions)

    def update_status(self, status, filename, status_text, count=None):
        self.file_label.configure(text=f"File: {filename}")
        self.status_label.configure(text=f"Status: {status_text}")
        if count is not None:
            self.records_label.configure(text=f"Records: {count:,}")
        else:
            self.records_label.configure(text="Records: -")

    def show_logs(self, logs):
        if logs:
            self.logs_textbox.delete("1.0", "end")
            self.logs_textbox.insert("1.0", logs)
            self.show_section(self.logs_frame)

    def show_results(self, data):
        self.show_section(self.results_frame)

        if self.current_format == "csv":
            lines = data.split('\n')
            lines = [line for line in lines if line.strip()]
            record_count = max(0, len(lines) - 1)  # -1 for header
            self.results_summary.configure(text=f"{record_count} records ready to export")

            # Show preview (first 4 lines including header)
            preview_lines = lines[:4]
            preview_text = '\n'.join(preview_lines)
        else:
            record_count = len(data) if isinstance(data, list) else 1
            self.results_summary.configure(text=f"{record_count} records ready to export")

            # Show preview (first 3 items)
            preview = data[:3] if isinstance(data, list) else [data]
            preview_text = json.dumps(preview, indent=2, ensure_ascii=False)

        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", preview_text)

    def save_file(self):
        if not self.current_data:
            return

        # Generate suggested filename
        base_name = self.current_filename.replace('.ndjson', '').replace('.json',
                                                                         '') if self.current_filename else 'parsed_output'
        extension = "csv" if self.current_format == "csv" else "json"
        suggested_name = f"{base_name}_parsed.{extension}"

        file_path = filedialog.asksavedialog(
            title="Save parsed file",
            defaultextension=f".{extension}",
            filetypes=[
                (f"{extension.upper()} files", f"*.{extension}"),
                ("All files", "*.*")
            ],
            initialvalue=suggested_name
        )

        if file_path:
            try:
                if self.current_format == "csv":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_data)
                else:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Success", f"File saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def copy_to_clipboard(self):
        if not self.current_data:
            return

        try:
            if self.current_format == "csv":
                text_to_copy = self.current_data
            else:
                text_to_copy = json.dumps(self.current_data, indent=2, ensure_ascii=False)

            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            self.root.update()  # Required for clipboard to work

            format_name = self.current_format.upper()
            messagebox.showinfo("Success", f"{format_name} copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Copy failed: {str(e)}")

    def cleanup_temp_file(self):
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                os.remove(self.current_temp_file)
            except Exception:
                pass  # Ignore cleanup errors
            self.current_temp_file = None

    def show_section(self, section):
        section.pack(fill="x", padx=20, pady=10)

    def hide_section(self, section):
        section.pack_forget()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.cleanup_temp_file()
        self.root.destroy()


if __name__ == "__main__":
    app = ZSParserApp()
    app.run()