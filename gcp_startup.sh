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

# 2. Install NVIDIA Driver 535
echo "🔌 Installing certified NVIDIA GPU Drivers (v535)..."
apt-get install -y nvidia-driver-535 nvidia-utils-535
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️ Warning: nvidia-smi not detected immediately. A system reboot might be required."
else
    echo "✅ NVIDIA Drivers installed successfully."
    nvidia-smi
fi

# 3. Install Docker & Docker Compose
echo "🐳 Installing Docker Engine and Docker Compose..."
apt-get install -y docker.io docker-compose
systemctl start docker
systemctl enable docker
echo "✅ Docker setup completed."

# 4. Install NVIDIA Container Toolkit (allows Docker to access GPU VRAM)
echo "🛠️ Installing NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update -y
apt-get install -y nvidia-container-toolkit

# Configure Docker daemon to recognize NVIDIA GPU runtime
echo "🔧 Configuring Docker runtime to use NVIDIA driver..."
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
echo "✅ NVIDIA Container Toolkit configured."

# 5. Clone Repository
echo "🧬 Cloning IMAM AI repository..."
rm -rf /opt/Beta-V2
git clone https://github.com/netizen2812/Beta-V2.git /opt/Beta-V2
cd /opt/Beta-V2

# 6. Retrieve Secrets from GCP Custom Instance Metadata
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

# 7. Start the Infrastructure with Docker Compose
echo "🚀 Booting the Dockerized Node.js Backend & GPU AI Bridge..."
docker-compose up -d --build

echo "🎉 IMAM AI GCE VM Setup Script Executed Successfully!"
date
