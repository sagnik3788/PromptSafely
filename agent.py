import os
import hmac
import hashlib
import tempfile
import shutil
import re
from datetime import datetime
from urllib.parse import quote_plus
from typing import Optional

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from git import Repo, GitCommandError
import logging

# Minimal configuration via env vars
MANIFEST_REPO_HTTP = os.getenv(
    "MANIFEST_REPO_HTTP", "git@github.com:sagnik3788/PromptSafely-infra.git"
)
GIT_TOKEN = os.getenv("GIT_TOKEN")  # set if you want to use HTTPS auth (not required if using SSH deploy key)
TARGET_BRANCH = os.getenv("TARGET_BRANCH", "staging")
TARGET_FILE = os.getenv("TARGET_FILE", "envs/staging.tfvars")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
GIT_USER = os.getenv("GIT_USER", "sagnik3788")
GIT_EMAIL = os.getenv("GIT_EMAIL", "sagnikdas5432@gmail.com")
IMAGE_FIELD_REGEX = os.getenv("IMAGE_FIELD_REGEX", r'^\s*image\s*=\s*["\'].*["\']\s*$')

# SSH deploy key to use for git (optional). If repo url is SSH (git@...), this is used automatically.
SSH_KEY_PATH = os.path.expanduser(os.getenv("SSH_KEY_PATH", "~/.ssh/promptbot_deploy"))

if not MANIFEST_REPO_HTTP:
    raise SystemExit("Required env var: MANIFEST_REPO_HTTP")

# logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("agent")

app = FastAPI()


def verify_webhook_signature(secret: str, body: bytes, signature_header: Optional[str]) -> bool:
    if not signature_header:
        logger.debug("No signature header provided")
        return False
    sig = signature_header.strip()
    if sig.startswith("sha1="):
        algo, hexsig = "sha1", sig.split("=", 1)[1]
    elif sig.startswith("sha256="):
        algo, hexsig = "sha256", sig.split("=", 1)[1]
    else:
        algo, hexsig = None, sig

    def hmac_hex(a):
        return hmac.new(secret.encode(), body, getattr(hashlib, a)).hexdigest()

    if algo:
        return hmac.compare_digest(hmac_hex(algo), hexsig)
    return any(hmac.compare_digest(hmac_hex(a), hexsig) for a in ("sha1", "sha256"))


def build_image_ref(repo_name: str, tag: Optional[str], digest: Optional[str]) -> str:
    if digest:
        return f"{repo_name}@{digest if digest.startswith('sha256:') else 'sha256:' + digest}"
    return f"{repo_name}:{tag or 'latest'}"


def ensure_ssh_key_in_env(repo_url: str):
    """
    If repo_url is an SSH url (git@...), ensure GIT_SSH_COMMAND uses the configured SSH key.
    """
    if repo_url.startswith("git@") or repo_url.startswith("ssh://"):
        if not os.path.exists(SSH_KEY_PATH):
            logger.warning("SSH repo requested but SSH key not found at %s; git operations may fail", SSH_KEY_PATH)
            return
        # ensure git uses the given key for SSH ops
        os.environ["GIT_SSH_COMMAND"] = f"ssh -i {SSH_KEY_PATH} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
        logger.debug("Using SSH key for git operations (not printing path for security).")


def http_token_url(repo_http: str, token: str) -> str:
    """
    Build HTTPS URL embedding token in a way that GitHub accepts reliably.
    """
    if not token:
        return repo_http
    if repo_http.startswith("https://"):
        rest = repo_http[len("https://") :]
        # use x-access-token as username — reliable for PATs
        return f"https://x-access-token:{quote_plus(token)}@{rest}"
    return repo_http


def update_tfvars_and_push(repo_http: str, token: Optional[str], branch: str, target_file: str, image_ref: str):
    tmpdir = tempfile.mkdtemp(prefix="manifest_repo_")
    try:
        # If SSH repo configured, ensure SSH key env is set
        ensure_ssh_key_in_env(repo_http)

        # If HTTPS + token present, create a token-embedded URL for clone/push.
        repo_with_token = repo_http
        if repo_http.startswith("https://"):
            if token:
                repo_with_token = http_token_url(repo_http, token)
            else:
                logger.info("Cloning over HTTPS without token (read-only or credential helper may be required).")

        logger.info("Cloning manifest repo %s (branch=%s)", repo_http, branch)
        try:
            repo = Repo.clone_from(repo_with_token, tmpdir, branch=branch)
        except GitCommandError as e:
            # If the requested branch doesn't exist, clone default branch and create it locally
            msg = str(e)
            logger.warning("Clone with branch '%s' failed: %s", branch, msg)
            if "Remote branch" in msg or "not found" in msg:
                logger.info("Falling back to clone default branch and creating '%s' locally", branch)
                repo = Repo.clone_from(repo_with_token, tmpdir)
                # create new branch locally
                repo.git.checkout("-b", branch)
            else:
                # re-raise for other git errors
                raise

        # If cloning used HTTPS+token, ensure origin uses the token-embedded URL to authenticate push
        if repo_http.startswith("https://") and token:
            try:
                repo.remotes.origin.set_url(repo_with_token)
                logger.debug("Set origin URL to token-embedded HTTPS URL for authenticated push")
            except Exception:
                logger.debug("Failed to set origin URL to token-embedded URL; continuing")

        # If cloning used SSH, we don't change origin URL (will use ssh)
        with repo.config_writer() as cw:
            cw.set_value("user", "name", GIT_USER)
            cw.set_value("user", "email", GIT_EMAIL)

        target_path = os.path.join(tmpdir, target_file)
        logger.debug("Looking for target file at %s", target_path)
        if not os.path.exists(target_path):
            logger.error("Target file not found: %s", target_path)
            raise FileNotFoundError(f"Target file not found: {target_file}")

        with open(target_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        if image_ref in content:
            logger.info("Image %s already present in %s; skipping.", image_ref, target_file)
            return {"status": "skipped", "reason": "already_present"}

        pattern = re.compile(IMAGE_FIELD_REGEX, re.MULTILINE)
        new_line = f'image = "{image_ref}"\n'
        if pattern.search(content):
            logger.debug("Replacing existing image line in %s", target_file)
            # replace only the line, keep the rest of the file intact
            new_content = pattern.sub(new_line.strip(), content)
            if not new_content.endswith("\n"):
                new_content += "\n"
        else:
            logger.debug("No matching image line found; appending to %s", target_file)
            # append the image line to the end of the file
            if not content.endswith("\n"):
                content += "\n"
            new_content = content + new_line

        with open(target_path, "w", encoding="utf-8") as fh:
            fh.write(new_content)

        repo.index.add([target_file])
        commit_message = (
            f"{branch}: deploy image {image_ref}\n\nsource: dockerhub webhook\n"
            f"timestamp: {datetime.utcnow().isoformat()}Z\n"
        )
        repo.index.commit(commit_message)

        origin = repo.remote(name="origin")
        logger.info("Pushing commit to %s:%s", repo_http, branch)
        try:
            # Push and capture result for better logging
            push_info = origin.push(refspec=f"HEAD:{branch}")
            logger.debug("Push info: %s", push_info)
        except GitCommandError as e:
            msg = str(e)
            logger.error("Push failed: %s", msg)
            if "403" in msg or "permission" in msg.lower() or "denied" in msg.lower():
                logger.error("Push failed with permission error - check deploy key or GIT_TOKEN and branch protection rules")
            raise

        new_sha = repo.head.commit.hexsha
        logger.info("Pushed commit %s", new_sha)
        return {"status": "pushed", "commit": new_sha}
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass


@app.post("/hook/dockerhub")
async def handle_dockerhub(request: Request, x_hub_signature: Optional[str] = Header(None)):
    body = await request.body()
    logger.info("Received webhook request from %s", request.client.host if request.client else "unknown")
    if WEBHOOK_SECRET and not verify_webhook_signature(WEBHOOK_SECRET, body, x_hub_signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = await request.json()
    except Exception as e:
        logger.exception("Failed to parse JSON payload: %s", e)
        raise HTTPException(status_code=400, detail="invalid json")

    repo_name = payload.get("repository", {}).get("repo_name") or payload.get("repository", {}).get("name")
    push_data = payload.get("push_data", {}) or {}
    tag = push_data.get("tag")
    digest = push_data.get("digest")

    if not repo_name:
        logger.warning("Webhook payload missing repository name")
        raise HTTPException(status_code=400, detail="missing repository name")

    image_ref = build_image_ref(repo_name, tag, digest)
    logger.info("Processing image update: %s", image_ref)
    try:
        result = update_tfvars_and_push(MANIFEST_REPO_HTTP, GIT_TOKEN, TARGET_BRANCH, TARGET_FILE, image_ref)
        logger.info("Update result: %s", result)
    except FileNotFoundError as e:
        logger.exception("Target file error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    except GitCommandError as e:
        logger.exception("Git error: %s", e)
        raise HTTPException(status_code=500, detail="git error")
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="unexpected error")

    return JSONResponse(result)
