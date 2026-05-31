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

# 3b. Restore large seed files from GCS (these are in .gitignore so git doesn't track them)
# This runs on EVERY boot including preemption restarts to ensure data is always present.
echo "🗃️ Restoring seed data from GCS bucket gs://imam-ai-seed-data/..."
DATA_DIR="/opt/Beta-V2/ai_bridge/data"

# Restore phonetic cache (7.6MB)
if [ ! -f "$DATA_DIR/phonetic_cache.json" ]; then
  echo "  Downloading phonetic_cache.json..."
  gsutil cp gs://imam-ai-seed-data/phonetic_cache.json "$DATA_DIR/phonetic_cache.json"
  chmod 777 "$DATA_DIR/phonetic_cache.json"
  echo "  ✅ phonetic_cache.json restored."
else
  echo "  ✅ phonetic_cache.json already present."
fi

# Restore ChromaDB (28MB zip -> ~40MB extracted)
CHROMA_COMPLETE_FLAG="$DATA_DIR/chroma_db/build_complete.flag"
if [ ! -f "$CHROMA_COMPLETE_FLAG" ]; then
  echo "  Downloading and extracting chroma_db.zip (~100MB)..."
  gsutil cp gs://imam-ai-seed-data/chroma_db.zip /tmp/chroma_db.zip
  rm -rf "$DATA_DIR/chroma_db"
  unzip -o /tmp/chroma_db.zip -d /tmp/chroma_extract
  # Handle both zip structures (with or without ai_bridge/data prefix)
  if [ -d "/tmp/chroma_extract/ai_bridge/data/chroma_db" ]; then
    mv /tmp/chroma_extract/ai_bridge/data/chroma_db "$DATA_DIR/chroma_db"
  else
    mv /tmp/chroma_extract/chroma_db "$DATA_DIR/chroma_db"
  fi
  chmod -R 777 "$DATA_DIR/chroma_db"
  rm -f /tmp/chroma_db.zip
  rm -rf /tmp/chroma_extract
  echo "  ✅ chroma_db restored."
else
  echo "  ✅ chroma_db already present."
fi

echo "✅ GCS seed data restore complete."

# 4. Retrieve Secrets from GCP Custom Instance Metadata
# Store secrets via: gcloud compute instances add-metadata INSTANCE_NAME \
#   --metadata gemini-api-key=XXX,openrouter-api-key=XXX,mongo-uri=XXX,
#              internal-api-key=XXX,clerk-secret-key=XXX,
#              elevenlabs-api-key=XXX,elevenlabs-voice-id=XXX
echo "🔑 Injecting configuration credentials from GCP Metadata Server..."
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
HEADERS="Metadata-Flavor: Google"

GEMINI_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/gemini-api-key")
OPENROUTER_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/openrouter-api-key")
MONGO_URI=$(curl -s -H "$HEADERS" "$METADATA_URL/mongo-uri")
INTERNAL_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/internal-api-key")

# FIX: These were missing — all authenticated routes (Clerk) and TTS fallback
# (ElevenLabs) were failing silently in production.
CLERK_SECRET_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/clerk-secret-key")
ELEVENLABS_API_KEY=$(curl -s -H "$HEADERS" "$METADATA_URL/elevenlabs-api-key")
ELEVENLABS_VOICE_ID=$(curl -s -H "$HEADERS" "$METADATA_URL/elevenlabs-voice-id")

# Fallback placeholders if metadata not set
[ -z "$GEMINI_API_KEY" ]        && GEMINI_API_KEY="INSERT_YOUR_GEMINI_API_KEY_HERE"
[ -z "$OPENROUTER_API_KEY" ]    && OPENROUTER_API_KEY="INSERT_YOUR_OPENROUTER_API_KEY_HERE"
[ -z "$MONGO_URI" ]             && MONGO_URI="mongodb+srv://..."
[ -z "$INTERNAL_API_KEY" ]      && INTERNAL_API_KEY="faith_tech_secret_key_2026"
[ -z "$CLERK_SECRET_KEY" ]      && CLERK_SECRET_KEY="INSERT_CLERK_SECRET_KEY_HERE"
[ -z "$ELEVENLABS_API_KEY" ]    && ELEVENLABS_API_KEY=""
[ -z "$ELEVENLABS_VOICE_ID" ]   && ELEVENLABS_VOICE_ID="pNInz6obpgDQGcFmaJgB"

# Write standard runtime .env file
# FIX: Added CLERK_SECRET_KEY, ELEVENLABS keys, ALLOWED_ORIGINS, FRONTEND_URL
cat <<EOT > /opt/Beta-V2/.env
PORT=5001
MONGO_URI=${MONGO_URI}
GEMINI_API_KEY=${GEMINI_API_KEY}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
INTERNAL_API_KEY=${INTERNAL_API_KEY}
AI_BRIDGE_URL=http://ai-bridge:8000

# Clerk authentication — required by requireAuth middleware
CLERK_SECRET_KEY=${CLERK_SECRET_KEY}

# ElevenLabs TTS fallback
ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
ELEVENLABS_VOICE_ID=${ELEVENLABS_VOICE_ID}

# CORS — AI Bridge allows these origins (Express handles its own CORS separately)
ALLOWED_ORIGINS=https://www.imamapp.co,https://imamapp.co,https://tryimam.vercel.app,http://localhost:3000

# Frontend URL for Daily.co webhook and CORS
FRONTEND_URL=https://www.imamapp.co
NODE_ENV=production
EOT

echo "✅ Environment variables configured at /opt/Beta-V2/.env."

# ── GCP Firewall check ────────────────────────────────────────────────────────
# FIX: Port 5001 must be open for Vercel to reach the Node backend.
# Run this ONCE from your local machine (not this script — needs IAM permission):
#
#   gcloud compute firewall-rules create allow-imam-api \
#     --direction=INGRESS --priority=1000 --network=default \
#     --action=ALLOW --rules=tcp:5001 \
#     --source-ranges=0.0.0.0/0 \
#     --target-tags=imam-ai-server \
#     --description="Allow IMAM AI Express backend from Vercel"
#
#   gcloud compute instances add-tags INSTANCE_NAME \
#     --tags=imam-ai-server --zone=ZONE
#
# Also reserve a static external IP to avoid IP changes on spot VM preemption:
#   gcloud compute addresses create imam-ai-static-ip --region=REGION
#   gcloud compute instances delete-access-config INSTANCE_NAME --zone=ZONE \
#     --access-config-name="External NAT"
#   gcloud compute instances add-access-config INSTANCE_NAME --zone=ZONE \
#     --access-config-name="External NAT" \
#     --address=$(gcloud compute addresses describe imam-ai-static-ip --region=REGION --format='value(address)')
echo "⚠️  Remember: GCP firewall rule for port 5001 must be created manually once."
echo "⚠️  Recommend reserving a static external IP to survive preemption restarts."

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
