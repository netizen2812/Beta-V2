
$PROJECT_ID = "1083361407878"
$REGION = "us-central1"
$BUCKET = "gs://maulana-urdu-forge-project-ffb3710a"

function Launch-Job($lang, $version, $zip_path, $output_dir) {
    $displayName = "maulana-$lang-xtts-$version"
    # Ultra-hardened installation sequence to avoid SIGSEGV
    $command = "export USE_XLA=0`nunset PJRT_DEVICE`nexport PYTHONNOUSERSITE=1`n" +
               "pip install --upgrade pip setuptools wheel`n" +
               # Install TTS first to let it bring its dependencies, then we fix torch
               "pip install --no-cache-dir TTS==0.22.0 python-json-logger`n" +
               "pip install --no-cache-dir transformers==4.38.0 accelerate==0.27.2`n" +
               # Final torch environment fix to ensure CUDA compatibility
               "pip install --no-cache-dir --force-reinstall torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121`n" +
               "gcloud storage cp $BUCKET/train_xtts_gcp.py /tmp/train.py`n" +
               "python3 /tmp/train.py --lang=$lang --zip_path=$zip_path --output_dir=$output_dir --steps=5000 --batch_size=2 --lr=5e-6"

    $indentedCommand = $command -replace "`n", "`n          "

    $yamlConfig = @"
workerPoolSpecs:
  - machineSpec:
      machineType: n1-standard-16 # Increased RAM to avoid OOM/SIGSEGV during build
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

# Launch English Job (v66)
Launch-Job "en" "v66" "$BUCKET/en_gcp_forge.zip" "$BUCKET/en_xtts_v66"

# Launch Arabic Job (v67)
Launch-Job "ar" "v67" "$BUCKET/ar_gcp_forge.zip" "$BUCKET/ar_xtts_v67"
