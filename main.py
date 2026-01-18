import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import re
import json
import requests

token = None
private_token = None
private_access_key = None
user_id = None
HEADERS = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "com.moodle.moodlemobile"}

# ========== CONFIG ==========
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

SITE = os.getenv("MOODLE_SITE")
WEBSERVICE_URL = f"{SITE}/webservice/rest/server.php"
USERNAME = os.getenv("MOODLE_USERNAME")
PASSWORD = os.getenv("MOODLE_PASSWORD")

# Basic env validation
if not SITE:
    print("Missing MOODLE_SITE in environment (.env).")
    sys.exit(1)

DUMP_ALL = False
FULL_SANITIZER = False

COURSE_ALIASES = {
    1678: "FMI",
    1679: "AM",
    1680: "PROI",
    1681: "SD",
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

    print(f"Attempting login to {SITE}...")
    try:
        response = requests.post(
            f"{SITE}/login/token.php?lang=en",
            headers=HEADERS,
            data={"username": username, "password": password, "service": "moodle_mobile_app"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            
            # Check for Moodle error responses
            if "error" in data:
                print(f"Login error: {data.get('error', 'Unknown error')}")
                if "errorcode" in data:
                    print(f"Error code: {data['errorcode']}")
                if "stacktrace" in data:
                    print(f"Details: {data.get('message', '')}")
                return False
            
            token = data.get("token")
            private_token = data.get("privatetoken")
            
            if not token:
                print("Error: No token received from server")
                print(f"Response data: {json.dumps(data, indent=2)}")
                return False
            
            print(f"✓ Token received: {token[:20]}...")
            return True
        else:
            print(f"HTTP error {response.status_code}: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("Error: Connection timeout. Check your internet connection and MOODLE_SITE URL.")
        return False
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to {SITE}. Check the URL in your .env file.")
        return False
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        return False


def post_webservice(function, arguments=None):
    global token

    params = {"moodlewsrestformat": "json", "wsfunction": function, "wstoken": token}

    if arguments:
        params.update(arguments)

    try:
        response = requests.post(
            WEBSERVICE_URL,
            params=params,
            headers=HEADERS,
            data={"moodlewssettingfilter": "true", "moodlewssettingfileurl": "true", "moodlewssettinglang": "en"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            
            # Check for Moodle error in response
            if isinstance(data, dict) and "exception" in data:
                print(f"\nAPI Error calling {function}:")
                print(f"  Exception: {data.get('exception', 'Unknown')}")
                print(f"  Message: {data.get('message', 'No message')}")
                if "errorcode" in data:
                    print(f"  Error code: {data['errorcode']}")
                return None
            
            return data
        else:
            print(f"HTTP {response.status_code} calling {function}: {response.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout calling {function}")
        return None
    except Exception as e:
        print(f"Error calling {function}: {e}")
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

    response = requests.post(WEBSERVICE_URL, headers=HEADERS, data=data)
    return response.json()


if __name__ == "__main__":
    if token is None:
        if USERNAME and PASSWORD:
            if login(USERNAME, PASSWORD):
                print("login successful!")
            else:
                print("login failed!")
                sys.exit(1)
        else:
            print("Missing MOODLE_USERNAME or MOODLE_PASSWORD. Set them in .env.")
            sys.exit(1)
    else:
        print("using token:", token)

    print("\nFetching site info...")
    site_info = get_site_info()

    if site_info is None:
        print("Failed to fetch site info. Check your credentials and permissions.")
        sys.exit(1)
    
    user_id = site_info.get("userid")
    private_access_key = site_info.get("userprivateaccesskey")
    
    if not user_id:
        print("Error: No user ID in site info")
        print(f"Site info: {json.dumps(site_info, indent=2)}")
        sys.exit(1)
    
    print(f"✓ User ID: {user_id}")
    if private_access_key:
        print(f"✓ Private access key: {private_access_key[:20]}...")
    else:
        print("⚠ Warning: No private access key (file downloads may fail)")

    print(f"\nFetching courses for user {user_id}...")
    courses = post_webservice("core_enrol_get_users_courses", {"userid": user_id, "returnusercount": "0"})

    if not courses:
        print("No courses found or error fetching courses.")
        sys.exit(1)
    
    print(f"✓ Found {len(courses)} course(s)\n")

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
        print(f"\n[{course_id}] Processing: {cleaned_name}")
        print(f"  → {course_dir}")

        contents = post_webservice("core_course_get_contents", {"courseid": course_id})
        
        if not contents:
            print(f"  ⚠ No contents found for course {course_id}")
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

                    file_url = content["fileurl"]
                    download_url = pluginfile_to_token_url(file_url, private_access_key)
                    if not download_url:
                        print("   skipping: missing access key or URL")
                        continue

                    print(f"    ↓ {file_name}")
                    try:
                        response = requests.get(download_url, headers=HEADERS, timeout=60)

                        if response.status_code == 200:
                            with open(target_path, "wb") as f:
                                f.write(response.content)
                            size_mb = len(response.content) / (1024 * 1024)
                            print(f"      ✓ {size_mb:.2f} MB")
                        else:
                            print(f"      ✗ HTTP {response.status_code}")
                    except Exception as e:
                        print(f"      ✗ Error: {e}")
