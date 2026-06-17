import subprocess, json, time, sys

# Real-time deployment monitor with direct output flushing
deployment_name_check = "azureml-integration-with-agents"
resource_group_check = "lab-azureml-integration-with-agents"
start_time = time.time()
max_wait = 1800  # 30 minutes

print(f"Monitoring deployment '{deployment_name_check}' in RG '{resource_group_check}'")
print(f"Max wait: {max_wait//60} minutes\n")
sys.stdout.flush()

for iteration in range(90):
    elapsed = time.time() - start_time
    cmd = f'az deployment group show -g {resource_group_check} -n {deployment_name_check} --query "{{state:properties.provisioningState, timestamp:properties.timestamp, error:properties.error.message}}" -o json'
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[{iteration+1:02d}/90] ERROR: {result.stderr}")
        sys.stdout.flush()
        time.sleep(20)
        continue
    
    try:
        data = json.loads(result.stdout.strip())
        state = data.get("state", "Unknown")
        timestamp = data.get("timestamp", "")
        error = data.get("error")
        
        elapsed_min = int(elapsed // 60)
        elapsed_sec = int(elapsed % 60)
        
        print(f"[{iteration+1:02d}/90] [{elapsed_min:02d}m {elapsed_sec:02d}s] state={state}")
        if timestamp:
            print(f"           timestamp={timestamp}")
        if error:
            print(f"           ERROR: {error}")
        sys.stdout.flush()
        
        if state.lower() == "succeeded":
            print("\n✓ DEPLOYMENT COMPLETED SUCCESSFULLY")
            sys.stdout.flush()
            break
        elif state.lower() in ["failed", "canceled"]:
            print(f"\n✗ DEPLOYMENT {state.upper()}")
            sys.stdout.flush()
            break
    except Exception as e:
        print(f"[{iteration+1:02d}/90] PARSE ERROR: {e}")
        sys.stdout.flush()
    
    if elapsed > max_wait:
        print(f"\n✗ TIMEOUT: Exceeded {max_wait//60} minute limit")
        sys.stdout.flush()
        break
    
    time.sleep(20)

print("\nMonitoring complete.")
sys.stdout.flush()
