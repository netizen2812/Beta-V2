
$PROJECT_ID = "1083361407878"
$REGION = "us-central1"
$BUCKET = "gs://maulana-urdu-forge-project-ffb3710a"

function Launch-Job($lang, $version, $zip_path, $output_dir) {
    $displayName = "maulana-$lang-xtts-$version"
    # Nuclear option for torch_xla crash
    $command = "export USE_XLA=0`n" +
               "export PJRT_DEVICE=CPU`n" + # Set to CPU instead of unsetting to satisfy the runtime check
               "export PYTHONNOUSERSITE=1`n" +
               "pip uninstall -y torch-xla`n" + # REMOVE the problematic module
               "pip install --upgrade pip setuptools wheel`n" +
               "pip install --no-cache-dir TTS==0.22.0 python-json-logger`n" +
               "pip install --no-cache-dir transformers==4.38.0 accelerate==0.27.2`n" +
               "pip install --no-cache-dir --force-reinstall torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121`n" +
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

# Launch English Job (v68)
Launch-Job "en" "v68" "$BUCKET/en_gcp_forge.zip" "$BUCKET/en_xtts_v68"

# Launch Arabic Job (v69)
Launch-Job "ar" "v69" "$BUCKET/ar_gcp_forge.zip" "$BUCKET/ar_xtts_v69"
