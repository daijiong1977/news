# Nginx & SSL Setup for news.6ray.com

This document describes how to configure Nginx reverse proxy and SSL/TLS for `news.6ray.com` using Let's Encrypt (Certbot).

## Architecture

```
Internet → AWS Security Group (80, 443, 22)
    ↓
Firewalld (80/tcp, 443/tcp allowed)
    ↓
Nginx (80/443) → Reverse Proxy → Flask App (127.0.0.1:5001)
    ↓
News Application (subscription_service_enhanced.py)
    ↓
SQLite Database (/var/www/news/subscriptions.db)
```

---

## Prerequisites

- Server: EC2 with RHEL 10.0 (or similar)
- SSH key: `~/Downloads/web1.pem`
- SSH user: `ec2-user`
- Server IP: `18.223.121.227`
- Domain: `news.6ray.com` (DNS must point to server IP)

---

## Step 1: SSH to Server and Prepare Directories

```bash
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

# Create directory for Let's Encrypt webroot
sudo mkdir -p /var/www/letsencrypt
sudo chown -R nginx:nginx /var/www/letsencrypt
sudo chmod 755 /var/www/letsencrypt

# Set SELinux context (for RHEL)
sudo chcon -R -t httpd_sys_content_t /var/www/letsencrypt
```

---

## Step 2: Copy Nginx Configuration Files

Copy the two Nginx config files from the repo to the server:

```bash
# On your local machine:
scp -i ~/Downloads/web1.pem /Users/jidai/news/deploy/nginx-news.6ray.com.conf ec2-user@18.223.121.227:/tmp/
scp -i ~/Downloads/web1.pem /Users/jidai/news/deploy/nginx-news.6ray.com-ssl.conf ec2-user@18.223.121.227:/tmp/

# Then on the server:
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

sudo cp /tmp/nginx-news.6ray.com.conf /etc/nginx/conf.d/news.6ray.com.conf
sudo cp /tmp/nginx-news.6ray.com-ssl.conf /etc/nginx/conf.d/news.6ray.com-ssl.conf

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Step 3: Install Certbot

```bash
# Create Python virtual environment for Certbot
sudo python3 -m venv /opt/certbot-venv

# Upgrade pip
sudo /opt/certbot-venv/bin/pip install --upgrade pip

# Install Certbot and Nginx plugin
sudo /opt/certbot-venv/bin/pip install certbot certbot-nginx
```

---

## Step 4: Request SSL Certificate

```bash
# Request certificate using webroot method
sudo /opt/certbot-venv/bin/certbot certonly \
  --webroot \
  -w /var/www/letsencrypt \
  -d news.6ray.com \
  --agree-tos \
  --non-interactive \
  -m admin@6ray.com
```

**Expected output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/news.6ray.com/fullchain.pem
Key is saved at: /etc/letsencrypt/live/news.6ray.com/privkey.pem
This certificate expires on [DATE].
```

---

## Step 5: Verify Certificate and Test HTTPS

```bash
# Verify certificate details
sudo openssl x509 -in /etc/letsencrypt/live/news.6ray.com/fullchain.pem -noout -text | grep -A 2 'Subject:'

# Test HTTPS locally on server
curl -I https://127.0.0.1/

# Test from your machine
curl -I https://news.6ray.com/
```

---

## Step 6: Configure Automatic Certificate Renewal

Add cron job to automatically renew certificates:

```bash
sudo crontab -e
```

Add this line:
```cron
0 3 * * * /opt/certbot-venv/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'
```

This runs daily at 3 AM and automatically reloads nginx if certificates are renewed.

---

## Step 7: Update AWS Security Group (Optional)

If not already configured, update the AWS EC2 Security Group to allow:
- **Port 80 (HTTP)** - from 0.0.0.0/0 (for ACME challenge and HTTP → HTTPS redirect)
- **Port 443 (HTTPS)** - from 0.0.0.0/0
- **Port 22 (SSH)** - from your IP only (for security)
- **Port 5001 (Flask)** - restricted or closed (only accessible via Nginx on localhost)

---

## Step 8: Update Firewall Rules (if using firewalld)

```bash
# Open HTTP and HTTPS
sudo firewall-cmd --zone=public --add-port=80/tcp --permanent
sudo firewall-cmd --zone=public --add-port=443/tcp --permanent
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --zone=public --list-ports
```

---

## Certificate Details

- **Authority:** Let's Encrypt
- **Certificate:** `/etc/letsencrypt/live/news.6ray.com/fullchain.pem`
- **Private Key:** `/etc/letsencrypt/live/news.6ray.com/privkey.pem`
- **Renewal:** Automatic (cron job runs daily at 3 AM)
- **Expiration:** 90 days (auto-renewed before expiry)

---

## Troubleshooting

### Certificate Request Fails

**Error:** `Certbot error: The server will not issue a certificate to the IP address alone.`

**Solution:** Ensure `news.6ray.com` DNS points to your server IP and is accessible from the internet.

### Nginx Shows 502 Bad Gateway

**Check:**
```bash
# Is the Flask app running?
sudo systemctl status news.service

# Check Nginx error logs
sudo tail -50 /var/log/nginx/error.log

# Check if Flask is listening on 5001
ss -ltnp | grep 5001
```

### HTTPS Not Working

**Verify:**
```bash
# Check certificate
sudo openssl x509 -in /etc/letsencrypt/live/news.6ray.com/fullchain.pem -noout -dates

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Check Nginx logs
sudo tail -50 /var/log/nginx/error.log
```

### Port 443 Not Accessible

**Check firewall:**
```bash
sudo firewall-cmd --zone=public --list-ports
sudo firewall-cmd --zone=public --list-services
```

---

## Quick Reference Commands

```bash
# SSH to server
ssh -i ~/Downloads/web1.pem ec2-user@18.223.121.227

# Check Nginx status
sudo systemctl status nginx

# Reload Nginx (after config changes)
sudo systemctl reload nginx

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Renew certificate manually
sudo /opt/certbot-venv/bin/certbot renew --webroot -w /var/www/letsencrypt

# Check certificate expiration
sudo openssl x509 -in /etc/letsencrypt/live/news.6ray.com/fullchain.pem -noout -dates

# Restart Flask app
sudo systemctl restart news.service

# View Flask logs
sudo journalctl -u news.service -f
```

---

## Next Steps

1. **Verify HTTPS:** Visit `https://news.6ray.com` in your browser
2. **Test API:** `curl https://news.6ray.com/api/article-content?article_id=1&difficulty=high&language=en`
3. **Monitor logs:** Watch Nginx and Flask logs for errors
4. **Backup config:** Keep a backup of `/etc/nginx/conf.d/news*.conf`
5. **Set up monitoring:** Consider adding uptime monitoring or alerting

---

**Last Updated:** October 20, 2025
