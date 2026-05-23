
$PROJECT_ID = "1083361407878"
$REGION = "us-central1"
$BUCKET = "gs://maulana-urdu-forge-project-ffb3710a"

# Upload the training script to GCS first
gcloud storage cp ai_bridge/scripts/train_xtts_gcp.py "$BUCKET/train_xtts_gcp.py"

function Launch-Job($lang, $version, $zip_path, $output_dir) {
    $displayName = "maulana-$lang-xtts-$version"
    $command = "export USE_XLA=0`nunset PJRT_DEVICE`nexport PYTHONNOUSERSITE=1`n" +
               "pip install --no-cache-dir transformers==4.38.0 accelerate==0.27.2 python-json-logger`n" +
               "pip install --no-cache-dir TTS`n" +
               "pip install --no-cache-dir --force-reinstall torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121`n" +
               "gcloud storage cp $BUCKET/train_xtts_gcp.py /tmp/train.py`n" +
               "python3 /tmp/train.py --lang=$lang --zip_path=$zip_path --output_dir=$output_dir --steps=5000 --batch_size=2 --lr=5e-6"

    $indentedCommand = $command -replace "`n", "`n          "

    $yamlConfig = @"
workerPoolSpecs:
  - machineSpec:
      machineType: n1-standard-8
      acceleratorType: NVIDIA_TESLA_T4
      acceleratorCount: 1
    replicaCount: 1
    containerSpec:
      imageUri: us-docker.pkg.dev/vertex-ai/training/pytorch-gpu.2-2.py310:latest
      command:
        - bash
        - -c
      args:
        - |
          $indentedCommand
"@

    $yamlFile = "job_config_$version.yaml"
    $yamlConfig | Out-File -FilePath $yamlFile -Encoding utf8

    Write-Host "Launching $displayName in $REGION..."
    gcloud ai custom-jobs create `
        --region=$REGION `
        --display-name=$displayName `
        --config=$yamlFile
    
    Remove-Item $yamlFile
}

# Launch English Job
Launch-Job "en" "v64" "$BUCKET/en_gcp_forge.zip" "$BUCKET/en_xtts_v64"

# Launch Arabic Job
Launch-Job "ar" "v65" "$BUCKET/ar_gcp_forge.zip" "$BUCKET/ar_xtts_v65"
