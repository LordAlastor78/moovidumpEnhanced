#!/usr/bin/env python3
"""
Run script that sets up everything and executes the main script.
"""
import subprocess
import sys
import os
from pathlib import Path
import getpass
import logging
def prompt_credentials(default_site="https://moovi.uvigo.gal"):
    """Prompt user for site, username and password. Returns tuple (site, username, password)."""
    site_input = input(f"   MOODLE_SITE [{default_site}]: ").strip()
    site = site_input if site_input else default_site

    username = input("   MOODLE_USERNAME: ").strip()
    if not username:
        logger.error("   ❌ Username is required!")
        return None

    password = getpass.getpass("   MOODLE_PASSWORD: ")
    if not password:
        logger.error("   ❌ Password is required!")
        return None

    return site, username, password


def write_env_file(env_file, site, username, password=None):
    """Write `.env`. If password is None, write empty password field (not saved)."""
    try:
        pw_field = f'"{password}"' if password is not None else '""'
        env_content = f"""MOODLE_SITE="{site}"
MOODLE_USERNAME="{username}"
MOODLE_PASSWORD={pw_field}
"""
        env_file.write_text(env_content)
        return True
    except Exception as e:
        logger.error("   ❌ Error creating .env file: %s", e)
        return False

def main():
    # Get the directory of this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("run")

    logger.info("MooviDump Enhanced - Automatic Setup & Execution")

    # Step 1: Check .env and choose credential mode
    logger.info("\n[1/3] Checking .env file and credential mode...")
    env_file = script_dir / ".env"

    logger.info("Elige modo de credenciales:")
    logger.info("  1) Usar credenciales almacenadas en .env (si existe).")
    logger.info("  2) Introducir credenciales para esta ejecución (no guardar).")
    logger.info("  3) Introducir credenciales y guardarlas en .env.")
    mode = input("Modo [1/2/3]: ").strip() or "1"

    pw_for_run = None
    env_vars = None

    if mode == "1":
        if env_file.exists():
            logger.info("✓ .env file found; using stored credentials.")
        else:
            logger.info(".env no encontrada. Vamos a crearla ahora.")
            creds = prompt_credentials()
            if not creds:
                sys.exit(1)
            site, username, password = creds
            save = input("Guardar credenciales en .env? [y/N]: ").strip().lower() == "y"
            if save:
                if not write_env_file(env_file, site, username, password):
                    sys.exit(1)
                logger.info("\n✓ .env file created and credentials saved.")
            else:
                if not write_env_file(env_file, site, username, None):
                    sys.exit(1)
                pw_for_run = password
                logger.info("\n✓ .env file created (password not saved).")

    elif mode == "2":
        creds = prompt_credentials()
        if not creds:
            sys.exit(1)
        site, username, password = creds
        env_vars = {"MOODLE_SITE": site, "MOODLE_USERNAME": username, "MOODLE_PASSWORD": password}
        logger.info("Using temporary credentials for this run (not saved).")

    elif mode == "3":
        creds = prompt_credentials()
        if not creds:
            sys.exit(1)
        site, username, password = creds
        if not write_env_file(env_file, site, username, password):
            sys.exit(1)
        logger.info("\n✓ .env file created and credentials saved.")
    else:
        logger.error("Modo inválido.")
        sys.exit(1)

    # Step 2: Install requirements
    logger.info("\n[2/3] Installing dependencies...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("✓ Dependencies installed successfully")
        else:
            logger.warning("Some dependencies may have failed to install")
            logger.debug(result.stderr)
    except Exception as e:
        logger.error("❌ Error installing dependencies: %s", e)
        sys.exit(1)

    # Step 3: Run main.py
    logger.info("\n[3/3] Running main.py...")
    logger.info("-" * 60)
    try:
        # Build child environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        if pw_for_run:
            env["MOODLE_PASSWORD"] = pw_for_run

        force = input("Forzar redescarga de archivos existentes? [y/N]: ").strip().lower() == "y"
        cmd = [sys.executable, "main.py"]
        if force:
            cmd.append("--force")
        logger.info("Launching main.py... %s", "(force)" if force else "")
        result = subprocess.run(cmd, check=False, env=env)
        logger.info("main.py exited with code %s", result.returncode)
        sys.exit(result.returncode)
    except Exception as e:
        logger.error("❌ Error running main.py: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
