Deploy README — news (news.6ray.com)

This repository now uses a very simple "git pull" deployment model by default. The server (news.6ray.com) will fetch updates from GitHub manually or via a lightweight trigger; there is no automatic SSH-based deploy from GitHub Actions in the normal push flow.

Goal
----
Keep server-side deployment minimal: the server runs a checked-out copy of the repo and updates are applied by running `git pull` on the server. This avoids storing private keys in GitHub secrets and keeps all runtime configuration on the server.

Quick server setup (one-time)
-----------------------------
Run these commands on the server (as the account that will run the site, e.g., `ec2-user`):

```bash
# create the deployment directory
sudo mkdir -p /var/www/news
sudo chown ec2-user:ec2-user /var/www/news

# clone the repo (use HTTPS if you prefer; update origin if you use SSH)
cd /var/www/news
git clone https://github.com/daijiong1977/news.git .

# (optional) create a systemd service for your app using the example file
# edit deploy/news.service.example -> /etc/systemd/system/news.service and set ExecStart
sudo cp deploy/news.service.example /etc/systemd/system/news.service
sudo systemctl daemon-reload
sudo systemctl enable --now news.service
sudo systemctl status news.service
```

Apply updates (manual)
----------------------
On the server, whenever you want to update to the latest `main` branch:

```bash
cd /var/www/news
git fetch origin main
git reset --hard origin/main
# if your service needs to be restarted after code changes:
sudo systemctl restart news.service
```

Notes:
- `git fetch && git reset --hard origin/main` ensures the working tree exactly matches the remote branch (useful if you run builds or have generated files). If you prefer a gentler update, use `git pull --ff-only`.
- Keep runtime configuration (database files, secrets, env files) outside the repo or in a `.env` file that is ignored by git. See the repository `.gitignore`.

Optional: automate pulls (choose one)
------------------------------------
1) Cron-based polling (simple, no open ports): add a cron job that runs `git pull` periodically.

Example (run every 5 minutes):

```cron
*/5 * * * * cd /var/www/news && git fetch origin main && git reset --hard origin/main && sudo systemctl restart news.service
```

2) Webhook + small receiver (secure, event-driven): run a tiny webhook listener on the server that verifies GitHub HMAC signature and executes a safe update script. This is optional; I can provide a minimal Flask webhook receiver and systemd unit if you want it.

3) Manual: SSH + `git pull` (what you said you prefer).

Safety and best practices
-------------------------
- Do not commit secrets (API keys, private keys) to the repository. Use environment variables or a `.env` file excluded via `.gitignore`.
- If you use SSH clones, create a deploy-only keypair and add the public key to `/home/ec2-user/.ssh/authorized_keys`.
- Use `git reset --hard origin/main` only when you accept discarding local changes. If you have runtime assets or uploaded files in the repo, move them to a separate persistent directory.
- If your app runs in a container (podman/docker), you may want the systemd unit to run `podman-compose` or similar; keep container images and runtime data outside the repo.

What I changed in this repo
---------------------------
- Simplified this README to recommend a `git pull` workflow as the default.
- If you want, I can also update or disable the GitHub Actions deploy workflow so it won't attempt SSH deploys on push. See `.github/workflows/deploy.yml`.

Enabling GitHub Actions SSH deploy (optional)
---------------------------------------------
If you prefer GitHub to push and trigger the deploy automatically, the repository includes a GitHub Actions workflow that will copy `deploy/deploy_news.sh` to the server and run it via SSH. To enable it you must add these repository secrets (Settings → Secrets → Actions):

- `EC2_HOST` — server IP or hostname (example: `18.223.121.227`)
- `EC2_USER` — user to SSH as (example: `ec2-user`)
- `EC2_PORT` — SSH port (usually `22`)
- `EC2_SSH_KEY` — the private key (PEM) contents for the deploy key (no passphrase preferred for Actions)

Guidance for keys:
- Create a deploy-only SSH keypair on your machine: `ssh-keygen -t ed25519 -f deploy_news_key`.
- Add the public key (`deploy_news_key.pub`) to `/home/ec2-user/.ssh/authorized_keys` on the server.
- Paste the private key (`deploy_news_key`) into `EC2_SSH_KEY` in GitHub Secrets (make sure to include newlines exactly as in the PEM file).

Once secrets are set, pushes to `main` will run the deploy workflow and execute `/usr/local/bin/deploy_news.sh` on the server as root (the workflow moves the script into place and runs it with `sudo`).

Security note: Use a deploy-only key and restrict its permissions on the server (e.g., limit allowed commands or use a dedicated deploy user). Rotate the key if it is ever exposed.

Next steps I can take (if you want):
- Convert the GitHub Action to a manual dispatch-only workflow (so nothing runs automatically on push).
- Provide a minimal webhook receiver + systemd example (Flask single-file) that runs `git pull` when triggered and verifies a secret.
- Create a short checklist for first-time server setup (SSL, nginx, firewall) tailored to `news.6ray.com`.
