$REGION = "us-central1"

Write-Host "Launching maulana-en-xtts-v74 in $REGION..."
gcloud ai custom-jobs create `
    --region=$REGION `
    --display-name="maulana-en-xtts-v74" `
    --config="ai_bridge/scripts/vertex_forge_v74_en.yaml"

Write-Host "Launching maulana-ar-xtts-v75 in $REGION..."
gcloud ai custom-jobs create `
    --region=$REGION `
    --display-name="maulana-ar-xtts-v75" `
    --config="ai_bridge/scripts/vertex_forge_v75_ar.yaml"
