"""MooviDump Enhanced - main module

This module logs into a Moodle instance (via the mobile webservice), enumerates
the user's courses and downloads course files into a local `dumps/` folder.

Key features:
- Supports interactive or .env-based credential modes (handled by `run.py`).
- Uses a requests `Session` with retries and timeouts for robustness.
- Skips files already present unless `--force` is provided.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import re
import json
import logging
import argparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import getpass
from rich.console import Console
from rich.table import Table

token = None
private_token = None
private_access_key = None
user_id = None
HEADERS = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "com.moodle.moodlemobile"}

# ========== CONFIG ==========
from dotenv import load_dotenv  # noqa: E402


# Network / runtime defaults
TIMEOUT = 30
RETRIES = 3
DOWNLOAD_TIMEOUT = 60

# Logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="MooviDump Enhanced")
    p.add_argument("--force", action="store_true", help="Force re-download of files even if present")
    p.add_argument("--verbose", action="store_true", help="Verbose logging (debug)")
    return p.parse_args()


# Setup requests session with retries
session = requests.Session()
retries = Retry(total=RETRIES, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])  # type: ignore
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update(HEADERS)


def prompt_for_credentials():
    """Prompt the user for site, username and password and export them to os.environ.

    This helper is used when the user chooses to provide credentials interactively
    instead of using `.env` or `example.env`.
    """
    site = input("MOODLE site URL (e.g. https://moovi.uvigo.gal): ").strip()
    username = input("MOODLE username: ").strip()
    password = getpass.getpass("MOODLE password: ")
    if site:
        os.environ["MOODLE_SITE"] = site
    if username:
        os.environ["MOODLE_USERNAME"] = username
    if password:
        os.environ["MOODLE_PASSWORD"] = password


def choose_config():
    """Load configuration from environment or prompt the user.

    Behavior:
    - If `MOODLE_*` variables are already present (e.g. from `.env`), they are used.
    - If an `example.env` file exists, the user can choose to load it or enter
      temporary credentials.
    - Placeholders in `example.env` force an interactive prompt to avoid accidental
      use of example values.
    """
    ex = Path("example.env")
    # Load local .env first (created by setup) so existing credentials are respected
    load_dotenv()
    # If all required env vars are already provided, use them (non-interactive/CI)
    if os.getenv("MOODLE_SITE") and os.getenv("MOODLE_USERNAME") and os.getenv("MOODLE_PASSWORD"):
        logger.info("Using credentials from environment/.env.")
        return

    if ex.exists():
        console.print("Se ha detectado `example.env`. Elige una opción:", style="yellow")
        console.print("  1) Usar example.env (valores de ejemplo).", style="dim")
        console.print("  2) Introducir credenciales para acceso temporal (no se guardan).", style="dim")
        choice = input("Opción [1/2]: ").strip() or "1"
        if choice == "1":
            load_dotenv(dotenv_path=ex)
            # If example.env contains placeholders, force prompt for credentials
            env_site = os.getenv("MOODLE_SITE", "")
            env_user = os.getenv("MOODLE_USERNAME", "")
            env_pass = os.getenv("MOODLE_PASSWORD", "")
            placeholders = ("PLACEHOLDER", "username", "password", "YOUR_")
            if (
                (not env_site)
                or (not env_user)
                or (not env_pass)
                or any(p in env_user.upper() for p in [ph.upper() for ph in placeholders])
                or any(p in env_pass.upper() for p in [ph.upper() for ph in placeholders])
            ):
                console.print("El example.env contiene valores de ejemplo o vacíos. Introduce credenciales reales:", style="red")
                prompt_for_credentials()
            else:
                logger.info("Cargado example.env.")
        else:
            prompt_for_credentials()
    else:
        logger.info("No se encontró example.env. Introduce credenciales para acceso temporal.")
        prompt_for_credentials()


# Parse CLI args early so verbose affects initial messages
args = parse_args()
if args.verbose:
    logger.setLevel(logging.DEBUG)

FORCE_DOWNLOAD = bool(getattr(args, "force", False))

choose_config()

SITE = os.getenv("MOODLE_SITE")
if not SITE:
    logger.error("Missing MOODLE_SITE in environment.")
    sys.exit(1)

# Normalize SITE to avoid double slashes when building URLs
SITE = SITE.rstrip("/")

WEBSERVICE_URL = f"{SITE}/webservice/rest/server.php"
USERNAME = os.getenv("MOODLE_USERNAME")
PASSWORD = os.getenv("MOODLE_PASSWORD")

DUMP_ALL = False
FULL_SANITIZER = False

COURSE_ALIASES = {
    1678: "FMI",
    1679: "AM",
    1680: "PROI",
    1681: "SD",
    1682: "TCL",
    1683: "AL",
    1684: "AEDI I",
    1685: "ACI I",
    1686: "PROII",
    1687: "Estadística",
    1689: "Sistemas Operativos I",
    1690: "Enxeñería de Software I",
    1691: "ACII",
    1692: "Sistemas Operativos II",
    1693: "Redes de Computadores I",
    1694: "Enxeñaría do Software II",
    1695: "Bases de datos I",
    1696: "Arquitecturas paralelas",
    1697: "Lóxica para a computación",
    1698: "Redes de computadoras II",
    1699: "Bases de datos II",
    1700: "Interfaces de usuario",
    1701: "Centros de datos",
    1702: "Dirección e xestión de proxectos",
    1703: "Teoría de autómatas e linguaxes formais",
    1704: "",


    # TODO add all the courses you want to dump here, using their course ID as key and the desired folder name as value.
    # If a course is not listed here, it will use its full name (sanitized) as folder name.
    # ...
}
# ========== CONFIG ==========


def sanitize(name, max_len=80):
    s = str(name).strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s)
    if FULL_SANITIZER:
        s = re.sub(r"\s+", "_", s)
    s = s.rstrip(" .")
    if len(s) > max_len:
        s = s[:max_len].rstrip(" .")
    return s or "item"


# /tokenpluginfile.php/{private_access_key}/{context_id}/mod_{"resource"|"folder"}/content/0/{file_name}
def pluginfile_to_token_url(file_url, private_access_key):
    if not file_url or not private_access_key:
        return None
    parsed = urlparse(file_url)
    new_path = parsed.path.replace("/webservice/pluginfile.php/", f"/tokenpluginfile.php/{private_access_key}/", 1)
    return urlunparse(parsed._replace(path=new_path, query=""))


def login(username, password):
    global token, private_token

    logger.info("Attempting login to %s...", SITE)
    try:
        response = session.post(
            f"{SITE}/login/token.php?lang=en",
            data={"username": username, "password": password, "service": "moodle_mobile_app"},
            timeout=TIMEOUT,
        )

        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error("Login: invalid JSON response")
                return False
            
            # Check for Moodle error responses
            if "error" in data:
                logger.error("Login error: %s", data.get('error', 'Unknown error'))
                if "errorcode" in data:
                    logger.debug("Error code: %s", data['errorcode'])
                if "stacktrace" in data:
                    logger.debug("Details: %s", data.get('message', ''))
                return False

            token = data.get("token")
            private_token = data.get("privatetoken")

            if not token:
                logger.error("No token received from server")
                logger.debug("Response data: %s", json.dumps(data, indent=2))
                return False

            logger.info("Token received: %s...", token[:20])
            return True
        else:
            logger.error("HTTP error %s: %s", response.status_code, response.text)
            return False
    except requests.exceptions.Timeout:
        logger.error("Connection timeout. Check your internet connection and MOODLE_SITE URL.")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to %s. Check the URL in your .env file.", SITE)
        return False
    except Exception as e:
        logger.exception("Unexpected error during login: %s", e)
        return False


def post_webservice(function, arguments=None):
    global token

    params = {"moodlewsrestformat": "json", "wsfunction": function, "wstoken": token}

    if arguments:
        params.update(arguments)

    try:
        response = session.post(
            WEBSERVICE_URL,
            params=params,
            data={"moodlewssettingfilter": "true", "moodlewssettingfileurl": "true", "moodlewssettinglang": "en"},
            timeout=TIMEOUT,
        )

        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.error("Invalid JSON from webservice %s", function)
                return None

            # Check for Moodle error in response
            if isinstance(data, dict) and "exception" in data:
                logger.error("API Error calling %s: %s", function, data.get('exception', 'Unknown'))
                logger.debug("API message: %s", data.get('message', 'No message'))
                if "errorcode" in data:
                    logger.debug("Error code: %s", data['errorcode'])
                return None

            return data
        else:
            logger.error("HTTP %s calling %s: %s", response.status_code, function, response.text[:200])
            return None
    except requests.exceptions.Timeout:
        logger.error("Timeout calling %s", function)
        return None
    except Exception as e:
        logger.exception("Error calling %s: %s", function, e)
        return None


def get_site_info():
    return post_webservice("core_webservice_get_site_info")


def call_moodle_mobile_functions(requests_list):
    global token

    data = {
        "moodlewsrestformat": "json",
        "wsfunction": "tool_mobile_call_external_functions",
        "wstoken": token,
        "moodlewssettinglang": "en",
    }

    for i, req in enumerate(requests_list):
        data[f"requests[{i}][function]"] = req["function"]
        data[f"requests[{i}][arguments]"] = json.dumps(req.get("arguments", {}))
        data[f"requests[{i}][settingfilter]"] = str(req.get("settingfilter", 1))
        data[f"requests[{i}][settingfileurl]"] = str(req.get("settingfileurl", 1))

    response = session.post(WEBSERVICE_URL, data=data, timeout=TIMEOUT)
    try:
        return response.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON from tool_mobile_call_external_functions")
        return None


if __name__ == "__main__":
    if token is None:
        if USERNAME and PASSWORD:
            if login(USERNAME, PASSWORD):
                logger.info("login successful")
            else:
                logger.error("login failed")
                sys.exit(1)
        else:
            logger.error("Missing MOODLE_USERNAME or MOODLE_PASSWORD. Set them in .env.")
            sys.exit(1)
    else:
        logger.debug("using token: %s...", (token or "")[:20])

    logger.info("Fetching site info...")
    site_info = get_site_info()

    if site_info is None:
        logger.error("Failed to fetch site info. Check your credentials and permissions.")
        sys.exit(1)

    user_id = site_info.get("userid")
    private_access_key = site_info.get("userprivateaccesskey")

    if not user_id:
        logger.error("No user ID in site info")
        logger.debug("Site info: %s", json.dumps(site_info, indent=2))
        sys.exit(1)

    logger.info("User ID: %s", user_id)
    if private_access_key:
        logger.info("Private access key available (truncated): %s...", private_access_key[:20])
    else:
        logger.warning("No private access key (file downloads may fail)")

    logger.info("Fetching courses for user %s...", user_id)
    courses = post_webservice("core_enrol_get_users_courses", {"userid": user_id, "returnusercount": "0"})

    if not courses:
        logger.error("No courses found or error fetching courses.")
        sys.exit(1)

    logger.info("Found %d course(s)", len(courses))

    # Present courses and ask whether to download all or select specific ones
    visible_courses = [c for c in courses if not c.get("hidden")]
    logger.info("Cursos disponibles:")
    table = Table(show_header=True, header_style="bold green")
    table.add_column("#", width=4)
    table.add_column("Course ID", width=10)
    table.add_column("Name")
    for i, c in enumerate(visible_courses, start=1):
        full_name = c.get("fullname", "") or ""
        display = (full_name.split(":", 1)[1].strip() if ":" in full_name else full_name.strip()) or f"course_{c.get('id')}"
        table.add_row(str(i), str(c.get('id')), display)
    console.print(table)

    choice = input("\nDescargar todos los cursos? [y/N]: ").strip().lower() or "n"
    if choice == "y":
        selected_ids = [c.get("id") for c in visible_courses]
    else:
        sel = input("Introduce números (1,2,3) o IDs separados por comas (vacío para cancelar): ").strip()
        if not sel:
            console.print("Operación cancelada.", style="yellow")
            sys.exit(0)
        parts = [p.strip() for p in sel.split(",") if p.strip()]
        selected_ids = set()
        for p in parts:
            if p.isdigit():
                # could be index or id; prefer index if within range
                idx = int(p)
                if 1 <= idx <= len(visible_courses):
                    selected_ids.add(visible_courses[idx - 1].get("id"))
                else:
                    selected_ids.add(int(p))
            else:
                try:
                    selected_ids.add(int(p))
                except ValueError:
                    pass
        selected_ids = list(selected_ids)

    # Filter courses to only selected ones
    courses = [c for c in courses if c.get("id") in (selected_ids or [])]

    dumps_dir = Path("dumps")
    dumps_dir.mkdir(parents=True, exist_ok=True)

    for course in courses or []:
        if course.get("hidden"):
            continue
        course_id = course["id"]
        alias = COURSE_ALIASES.get(course_id)
        if alias:
            cleaned_name = alias
        else:
            full_name = course.get("fullname", "") or ""
            cleaned_name = (full_name.split(":", 1)[1].strip() if ":" in full_name else full_name.strip()) or f"course_{course_id}"

        folder_name = sanitize(cleaned_name)
        if DUMP_ALL:
            folder_name = f"{course_id}_{sanitize(cleaned_name)}"
        course_dir = dumps_dir / folder_name
        course_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Processing course [%s] %s", course_id, cleaned_name)
        logger.debug("Output directory: %s", course_dir)

        contents = post_webservice("core_course_get_contents", {"courseid": course_id})
        
        if not contents:
            logger.warning("No contents found for course %s", course_id)
            continue

        if DUMP_ALL:
            with open(course_dir / "contents.json", "w", encoding="utf-8") as f:
                json.dump(contents, f, indent=2, ensure_ascii=False)

        sections_root = course_dir
        if DUMP_ALL:
            sections_root = course_dir / "sections"
        sections_root.mkdir(parents=True, exist_ok=True)

        for section in contents or []:
            section_number = section.get("section", 0)
            section_name = section.get("name")

            section_folder_name = sanitize(section_name)
            if DUMP_ALL:
                section_folder_name = f"{int(section_number):02d}_{sanitize(section_name)}"
            section_dir = sections_root / section_folder_name
            section_dir.mkdir(parents=True, exist_ok=True)

            if DUMP_ALL:
                with open(section_dir / "section.json", "w", encoding="utf-8") as f:
                    json.dump(section, f, indent=2, ensure_ascii=False)

            for module_index, module in enumerate(section.get("modules", [])):
                module_name = module.get("name")
                module_folder_name = sanitize(module_name)
                if DUMP_ALL:
                    module_folder_name = f"{module_index:03d}_{sanitize(module_name)}"
                module_dir = section_dir / module_folder_name
                module_dir.mkdir(parents=True, exist_ok=True)

                if DUMP_ALL:
                    with open(module_dir / "module.json", "w", encoding="utf-8") as f:
                        json.dump(module, f, indent=2, ensure_ascii=False)

                for content in module.get("contents", []):
                    if content.get("type") != "file":
                        continue

                    file_name = content.get("filename")
                    file_name = sanitize(file_name)
                    target_path = module_dir / file_name

                    # Skip download if file already exists (same name) unless forcing
                    if target_path.exists() and not FORCE_DOWNLOAD:
                        logger.info("Skipping download; file already exists: %s", target_path)
                        continue

                    file_url = content["fileurl"]
                    download_url = pluginfile_to_token_url(file_url, private_access_key)
                    if not download_url:
                        logger.warning("Skipping download: missing access key or URL for %s", file_name)
                        continue

                    console.print(f"[cyan]↓[/cyan] {file_name}")
                    try:
                        response = session.get(download_url, timeout=DOWNLOAD_TIMEOUT)

                        if response.status_code == 200:
                            with open(target_path, "wb") as f:
                                f.write(response.content)
                            size_mb = len(response.content) / (1024 * 1024)
                            logger.info("Downloaded %s (%.2f MB)", file_name, size_mb)
                        else:
                            logger.warning("HTTP %s when downloading %s", response.status_code, file_name)
                    except Exception as e:
                        logger.exception("Error downloading %s: %s", file_name, e)
