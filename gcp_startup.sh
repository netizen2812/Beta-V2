#!/bin/bash
# ==============================================================================
# IMAM AI — GCP Spot GPU GCE Instance Startup & Orchestration Script
# Target OS: Ubuntu 22.04 LTS (Minimal or Standard)
# Hardware: 1x NVIDIA Tesla T4 GPU
# ==============================================================================

# Set up logging
exec > >(tee -a /var/log/imam-ai-startup.log) 2>&1
echo "🚀 Starting IMAM AI Always-Warm GPU GCE VM setup..."
date

# 1. Update system libraries
echo "📦 Updating apt repositories..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# 2. Install Docker & Docker Compose
echo "🐳 Installing Docker Engine and Docker Compose..."
apt-get install -y docker.io docker-compose
systemctl start docker
systemctl enable docker
echo "✅ Docker setup completed."

# 3. Clone Repository (or pull latest if already exists — idempotent on preemption restart)
echo "🧬 Syncing IMAM AI repository..."
if [ -d "/opt/Beta-V2/.git" ]; then
  echo "  Repo already exists — pulling latest changes..."
  git -C /opt/Beta-V2 pull origin main
else
  echo "  Fresh clone..."
  git clone https://github.com/netizen2812/Beta-V2.git /opt/Beta-V2
fi
cd /opt/Beta-V2

# 4. Retrieve Secrets from GCP Custom Instance Metadata
echo "🔑 Injecting configuration credentials from GCP Metadata Server..."
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
HEADERS="Metadata-Flavor: Google"

GEMINI_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/gemini-api-key")
OPENROUTER_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/openrouter-api-key")
MONGO_URI=$(curl -s -H "$HEADERS" "$METADATA_URL/mongo-uri")
INTERNAL_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/internal-api-key")

# If metadata values are not provided, write helpful placeholders
[ -z "$GEMINI_API_KEY" ] && GEMINI_API_KEY="INSERT_YOUR_GEMINI_API_KEY_HERE"
[ -z "$OPENROUTER_API_KEY" ] && OPENROUTER_API_KEY="INSERT_YOUR_OPENROUTER_API_KEY_HERE"
[ -z "$MONGO_URI" ] && MONGO_URI="mongodb+srv://..."
[ -z "$INTERNAL_API_KEY" ] && INTERNAL_API_KEY="faith_tech_secret_key_2026"

# Write standard runtime .env file
cat <<EOT > /opt/Beta-V2/.env
PORT=5001
MONGO_URI=${MONGO_URI}
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
INTERNAL_API_KEY=${INTERNAL_API_KEY}
AI_BRIDGE_URL=http://ai-bridge:8000
EOT

echo "✅ Environment variables configured at /opt/Beta-V2/.env."

# 5. Install Docker Buildx (modern builder, avoids legacy warnings)
echo "🔧 Installing Docker Buildx plugin..."
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/buildx/releases/download/v0.16.2/buildx-v0.16.2.linux-amd64 \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
echo "✅ Docker Buildx installed."

# 6. Create a systemd service so docker-compose auto-restarts on preemption/reboot
echo "🛡️ Creating systemd auto-restart service for Imam AI..."
cat <<SERVICE > /etc/systemd/system/imam-ai.service
[Unit]
Description=Imam AI Docker Compose Stack
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/Beta-V2
ExecStart=/usr/bin/docker-compose up -d --build
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=900

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable imam-ai.service
echo "✅ Systemd service registered."

# 7. Start the Infrastructure with Docker Compose (detached via nohup — survives SSH disconnect)
echo "🚀 Booting the Dockerized Node.js Backend & CPU AI Bridge (in background)..."
nohup docker-compose -f /opt/Beta-V2/docker-compose.yml up -d --build \
  > /tmp/imam-docker-compose.log 2>&1 &

echo "🎉 IMAM AI GCE VM Setup Script Dispatched Successfully!"
echo "   Build is running in background. Check progress with:"
echo "   sudo cat /tmp/imam-docker-compose.log"
echo "   sudo docker ps"
date
