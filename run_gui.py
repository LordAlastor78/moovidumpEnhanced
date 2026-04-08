#!/usr/bin/env python3
"""Desktop launcher for MooviDump Enhanced.

This UI lets users provide credentials, choose whether to save them in .env,
and run main.py without opening a terminal window manually.
"""

from __future__ import annotations

import os
import queue
import runpy
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk


APP_TITLE = "MooviDump Enhanced"
DEFAULT_SITE = "https://moovi.uvigo.gal"


class MooviDumpApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x680")
        self.root.minsize(900, 620)

        if getattr(sys, "frozen", False):
            self.app_dir = Path(sys.executable).resolve().parent
            self.runtime_dir = Path(getattr(sys, "_MEIPASS", self.app_dir))
        else:
            self.app_dir = Path(__file__).resolve().parent
            self.runtime_dir = self.app_dir

        self.env_file = self.app_dir / ".env"
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None

        self.site_var = tk.StringVar(value=DEFAULT_SITE)
        self.user_var = tk.StringVar(value="")
        self.pass_var = tk.StringVar(value="")
        self.save_password_var = tk.BooleanVar(value=False)
        self.force_var = tk.BooleanVar(value=False)
        self.install_deps_var = tk.BooleanVar(value=not getattr(sys, "frozen", False))
        self.course_mode_var = tk.StringVar(value="all")
        self.course_ids_var = tk.StringVar(value="")

        self._build_styles()
        self._build_ui()
        self._load_existing_env()
        self.root.after(120, self._poll_output_queue)

    def _build_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        bg = "#f4f7fb"
        card = "#ffffff"
        accent = "#005a9e"
        text_main = "#1c2530"

        self.root.configure(bg=bg)

        style.configure("Root.TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("Title.TLabel", background=bg, foreground=text_main, font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=bg, foreground="#4b5b70", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=card, foreground=text_main, font=("Segoe UI", 11, "bold"))
        style.configure("CardText.TLabel", background=card, foreground=text_main, font=("Segoe UI", 10))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Primary.TButton", background=[("!disabled", accent)])

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, style="Root.TFrame", padding=16)
        root_frame.pack(fill="both", expand=True)

        title = ttk.Label(root_frame, text=APP_TITLE, style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root_frame,
            text="Descarga tus cursos con una interfaz visual: credenciales, opciones y logs en tiempo real.",
            style="Subtitle.TLabel",
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        card = ttk.Frame(root_frame, style="Card.TFrame", padding=16)
        card.pack(fill="x")

        ttk.Label(card, text="Credenciales", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(card, text="Moodle site", style="CardText.TLabel").grid(row=1, column=0, sticky="w", pady=(12, 4))
        self.site_entry = ttk.Entry(card, textvariable=self.site_var)
        self.site_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ttk.Label(card, text="Usuario", style="CardText.TLabel").grid(row=3, column=0, sticky="w", pady=(6, 4))
        self.user_entry = ttk.Entry(card, textvariable=self.user_var)
        self.user_entry.grid(row=4, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(card, text="Contraseña", style="CardText.TLabel").grid(row=3, column=1, sticky="w", pady=(6, 4))
        self.pass_entry = ttk.Entry(card, textvariable=self.pass_var, show="*")
        self.pass_entry.grid(row=4, column=1, sticky="ew")

        opts_frame = ttk.Frame(card, style="Card.TFrame")
        opts_frame.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 4))

        ttk.Checkbutton(opts_frame, text="Guardar contraseña en .env", variable=self.save_password_var).pack(anchor="w")
        ttk.Checkbutton(opts_frame, text="Forzar redescarga (--force)", variable=self.force_var).pack(anchor="w")
        deps_check = ttk.Checkbutton(opts_frame, text="Instalar dependencias antes de ejecutar", variable=self.install_deps_var)
        deps_check.pack(anchor="w")
        if getattr(sys, "frozen", False):
            deps_check.configure(state="disabled")

        course_frame = ttk.Frame(card, style="Card.TFrame")
        course_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 2))

        ttk.Label(course_frame, text="Selección de cursos", style="CardText.TLabel").pack(anchor="w")
        ttk.Radiobutton(
            course_frame,
            text="Descargar todos los cursos visibles",
            value="all",
            variable=self.course_mode_var,
            command=self._toggle_course_ids,
        ).pack(anchor="w", pady=(4, 0))
        ttk.Radiobutton(
            course_frame,
            text="Descargar solo IDs concretos",
            value="ids",
            variable=self.course_mode_var,
            command=self._toggle_course_ids,
        ).pack(anchor="w")

        self.course_ids_entry = ttk.Entry(course_frame, textvariable=self.course_ids_var)
        self.course_ids_entry.pack(fill="x", pady=(6, 0))
        self.course_hint = ttk.Label(course_frame, text="Ejemplo: 1684,1685,1702", style="CardText.TLabel")
        self.course_hint.pack(anchor="w")
        self._toggle_course_ids()

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        actions = ttk.Frame(root_frame, style="Root.TFrame")
        actions.pack(fill="x", pady=(12, 8))

        self.run_button = ttk.Button(actions, text="Ejecutar descarga", style="Primary.TButton", command=self._start_run)
        self.run_button.pack(side="left")

        self.stop_button = ttk.Button(actions, text="Detener", command=self._stop_run, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        self.clear_button = ttk.Button(actions, text="Limpiar log", command=self._clear_log)
        self.clear_button.pack(side="left", padx=(8, 0))

        log_card = ttk.Frame(root_frame, style="Card.TFrame", padding=12)
        log_card.pack(fill="both", expand=True)

        ttk.Label(log_card, text="Log de ejecución", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        self.log_text = tk.Text(
            log_card,
            wrap="word",
            height=22,
            bg="#0e1116",
            fg="#d9e1ec",
            insertbackground="#d9e1ec",
            font=("Consolas", 10),
            relief="flat",
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def _load_existing_env(self) -> None:
        if not self.env_file.exists():
            return

        data = self._parse_env_file(self.env_file)
        site = data.get("MOODLE_SITE")
        user = data.get("MOODLE_USERNAME")
        saved_password = data.get("MOODLE_PASSWORD", "")

        if site:
            self.site_var.set(site)
        if user:
            self.user_var.set(user)
        if saved_password:
            self.pass_var.set(saved_password)
            self.save_password_var.set(True)

    def _toggle_course_ids(self) -> None:
        if self.course_mode_var.get() == "ids":
            self.course_ids_entry.configure(state="normal")
        else:
            self.course_ids_entry.configure(state="disabled")

    @staticmethod
    def _parse_env_file(path: Path) -> dict[str, str]:
        data: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
        return data

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _write_env(self, site: str, username: str, password: str, save_password: bool) -> None:
        password_line = f'MOODLE_PASSWORD="{password}"' if save_password else 'MOODLE_PASSWORD=""'
        content = (
            f'MOODLE_SITE="{site}"\n'
            f'MOODLE_USERNAME="{username}"\n'
            f"{password_line}\n"
        )
        self.env_file.write_text(content, encoding="utf-8")

    def _start_run(self) -> None:
        if self.process is not None:
            return

        site = self.site_var.get().strip().rstrip("/")
        username = self.user_var.get().strip()
        password = self.pass_var.get()

        if not site or not username or not password:
            messagebox.showerror("Campos incompletos", "Debes rellenar site, usuario y contraseña.")
            return

        if self.course_mode_var.get() == "ids" and not self.course_ids_var.get().strip():
            messagebox.showerror("Cursos", "Indica IDs de cursos (separados por comas) o usa el modo 'todos'.")
            return

        try:
            self._write_env(site, username, password, self.save_password_var.get())
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo escribir .env: {exc}")
            return

        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._append_log("\n=== Nueva ejecución ===\n")
        self._append_log(f"Site: {site}\n")

        thread = threading.Thread(target=self._run_pipeline, args=(site, username, password), daemon=True)
        thread.start()

    def _run_pipeline(self, site: str, username: str, password: str) -> None:
        try:
            os.chdir(self.app_dir)

            if self.install_deps_var.get():
                self._run_command([
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements.txt",
                ], "Instalando dependencias...")

            env = os.environ.copy()
            env.update(
                {
                    "MOODLE_SITE": site,
                    "MOODLE_USERNAME": username,
                    "MOODLE_PASSWORD": password,
                }
            )

            if getattr(sys, "frozen", False):
                cmd = [sys.executable, "--cli-worker"]
            else:
                cmd = [sys.executable, "main.py"]

            if self.course_mode_var.get() == "all":
                cmd.append("--all-courses")
            else:
                cmd.extend(["--courses", self.course_ids_var.get().strip()])

            if self.force_var.get():
                cmd.append("--force")

            exit_code = self._run_command(cmd, "Ejecutando main.py...", env=env)
            self.output_queue.put(f"\nProceso finalizado con código {exit_code}.\n")
        except Exception as exc:
            self.output_queue.put(f"\nError inesperado: {exc}\n")
        finally:
            self.output_queue.put("__PROCESS_FINISHED__")

    def _run_command(self, cmd: list[str], header: str, env: dict[str, str] | None = None) -> int:
        self.output_queue.put(f"\n{header}\n")
        self.output_queue.put(f"$ {' '.join(cmd)}\n")

        self.process = subprocess.Popen(
            cmd,
            cwd=self.app_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.output_queue.put(line)

        self.process.wait()
        code = self.process.returncode
        self.process = None
        return int(code or 0)

    def _stop_run(self) -> None:
        if self.process is None:
            return
        try:
            self.process.terminate()
            self._append_log("\nProceso detenido por el usuario.\n")
        except Exception as exc:
            self._append_log(f"\nNo se pudo detener el proceso: {exc}\n")

    def _poll_output_queue(self) -> None:
        while True:
            try:
                line = self.output_queue.get_nowait()
            except queue.Empty:
                break

            if line == "__PROCESS_FINISHED__":
                self.run_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                continue

            self._append_log(line)

        self.root.after(120, self._poll_output_queue)


def main() -> None:
    if "--cli-worker" in sys.argv:
        worker_args = [arg for arg in sys.argv[1:] if arg != "--cli-worker"]
        run_cli_worker(worker_args)
        return

    root = tk.Tk()
    app = MooviDumpApp(root)
    root.mainloop()


def run_cli_worker(extra_args: list[str]) -> None:
    if getattr(sys, "frozen", False):
        runtime_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        app_dir = Path(sys.executable).resolve().parent
    else:
        runtime_dir = Path(__file__).resolve().parent
        app_dir = runtime_dir

    main_script = runtime_dir / "main.py"
    if not main_script.exists():
        print(f"ERROR: main.py no encontrado en {runtime_dir}")
        sys.exit(1)

    # Ensure output folders like dumps/ are created next to the launcher (.exe).
    os.chdir(app_dir)
    sys.argv = [str(main_script)] + extra_args
    runpy.run_path(str(main_script), run_name="__main__")


if __name__ == "__main__":
    main()
