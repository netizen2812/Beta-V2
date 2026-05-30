#!/bin/bash
# Write the systemd auto-restart service for Imam AI containers
cat > /etc/systemd/system/imam-ai.service << 'SVCEOF'
[Unit]
Description=Imam AI Docker Compose Stack
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/Beta-V2
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable imam-ai.service
echo "✅ imam-ai.service installed and enabled"
systemctl is-enabled imam-ai.service
