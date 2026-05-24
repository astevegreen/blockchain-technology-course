# Start-Lab.ps1 - Unified Blockchain Lab Launcher
# Usage:
#   .\start-lab.ps1 -Mode instructor              # Host the blockchain
#   .\start-lab.ps1 -Mode instructor -UseNgrok    # Host with ngrok tunnel
#   .\start-lab.ps1 -Mode student                 # Connect to instructor's blockchain

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("instructor", "student", "beacon-lab", "reset")]
    [string]$Mode,
    
    [switch]$UseNgrok = $false,
    [switch]$Reset = $false,
    
    # Student-mode parameters
    [string]$ContractAddress = "",
    [string]$RpcUrl = ""
)

# ============================================================================
# RESET MODE - Full classroom reset (clear blockchain, then optionally start instructor)
# ============================================================================
function Start-ResetMode {
    param([switch]$Quiet = $false)
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "   FULL CLASSROOM RESET" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    # Try to stop any process using port 8545 (Hardhat node)
    Write-Host ""
    Write-Host "[1/2] Stopping blockchain node (port 8545)..." -ForegroundColor Green
    $killed = $false
    try {
        $conn = Get-NetTCPConnection -LocalPort 8545 -ErrorAction SilentlyContinue
        if ($conn) {
            $conn | ForEach-Object {
                $pid = $_.OwningProcess
                if ($pid) {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Write-Host "   Stopped process $pid" -ForegroundColor Yellow
                    $killed = $true
                }
            }
        }
        if (-not $killed) {
            Write-Host "   No node running on 8545" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   Could not stop node: $_" -ForegroundColor Yellow
        Write-Host "   Close the Hardhat window manually." -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 2

    # Run reset script
    Write-Host ""
    Write-Host "[2/2] Clearing blockchain data..." -ForegroundColor Green
    npm run reset
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Reset script reported an issue." -ForegroundColor Yellow
    }

    if (-not $Quiet) {
        Write-Host ""
        Write-Host "==================================================" -ForegroundColor Green
        Write-Host "RESET COMPLETE" -ForegroundColor Green
        Write-Host "==================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Start fresh instructor mode:" -ForegroundColor Cyan
        Write-Host "  .\start-lab.ps1 -Mode instructor" -ForegroundColor White
        Write-Host ""
    }
}

# ============================================================================
# INSTRUCTOR MODE
# ============================================================================
function Start-InstructorMode {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "   INSTRUCTOR MODE - BLOCKCHAIN HOST" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    # Get Local IP Address
    $ipAddr = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi", "Ethernet" -ErrorAction SilentlyContinue | 
               Select-Object -ExpandProperty IPAddress | 
               Select-Object -First 1)

    if (-not $ipAddr) {
        Write-Host "Could not auto-detect IP. Using 127.0.0.1" -ForegroundColor Yellow
        $ipAddr = "127.0.0.1"
    }

    Write-Host "Your Local IP: $ipAddr" -ForegroundColor Green
    Write-Host "Students should connect to: http://$($ipAddr):8545" -ForegroundColor Yellow

    # Check if ngrok is available
    $hasNgrok = Get-Command ngrok -ErrorAction SilentlyContinue

    # 0. Optional reset before starting
    if ($Reset) {
        Write-Host ""
        Write-Host "Performing reset first..." -ForegroundColor Yellow
        Start-ResetMode -Quiet
        Write-Host "Continuing with instructor startup..." -ForegroundColor Green
        Write-Host ""
    }

    # 1. Start Hardhat Node in a new window
    Write-Host ""
    Write-Host "[1/6] Starting blockchain node..." -ForegroundColor Green
    Write-Host "  (A new window will open - KEEP IT OPEN for the lab to work)" -ForegroundColor Gray
    $labDir = (Get-Location).Path
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$labDir'; Write-Host 'BLOCKCHAIN NODE - Keep this window open!' -ForegroundColor Cyan; npm run chain" -WorkingDirectory $labDir

    # Wait for node to boot
    Write-Host "Waiting for node to start..." -ForegroundColor Yellow
    $maxAttempts = 60
    $attempt = 0
    $nodeReady = $false

    while ($attempt -lt $maxAttempts -and -not $nodeReady) {
        Start-Sleep -Seconds 1
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8545" -Method POST `
                -Body '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' `
                -ContentType "application/json" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200 -and $response.Content -match '"result"') {
                $nodeReady = $true
                Write-Host "`nNode is ready!" -ForegroundColor Green
            }
        }
        catch {
            Write-Host "." -NoNewline
        }
    }

    if (-not $nodeReady) {
        Write-Host "`nERROR: Blockchain node did not start. Check the Hardhat window for errors." -ForegroundColor Red
        Write-Host "  - Ensure no other process is using port 8545" -ForegroundColor Yellow
        Write-Host "  - Try: netstat -an | findstr 8545" -ForegroundColor Yellow
        exit 1
    }

    # Extra stabilization delay (node can report ready before fully accepting connections)
    Write-Host "Stabilizing connection..." -ForegroundColor Gray
    Start-Sleep -Seconds 3

    # 2. Deploy Contracts
    Write-Host ""
    Write-Host "[2/6] Deploying smart contracts..." -ForegroundColor Green
    $deployOutput = npm run deploy 2>&1 | Out-String
    Write-Host $deployOutput

    if ($deployOutput -match "ECONNREFUSED|Cannot connect to the network") {
        Write-Host "`nERROR: Cannot connect to blockchain. The node may have stopped or not fully started." -ForegroundColor Red
        Write-Host "  - Keep the Hardhat window OPEN (do not close it)" -ForegroundColor Yellow
        Write-Host "  - Wait 10 seconds and run again: .\start-lab.ps1 -Mode instructor" -ForegroundColor Yellow
        exit 1
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nERROR: Contract deployment failed." -ForegroundColor Red
        exit 1
    }

    # Extract Contract Address (deploy.js prints "✅ PoS Simulator deployed to: 0x...")
    $posAddr = ""
    if ($deployOutput -match "deployed to:?\s+(0x[a-fA-F0-9]{40})") {
        $posAddr = $matches[1]
    }
    # Fallback: read from CONTRACT_ADDRESS.txt (deploy.js always writes it)
    if (-not $posAddr -and (Test-Path "CONTRACT_ADDRESS.txt")) {
        $posAddr = (Get-Content "CONTRACT_ADDRESS.txt" -First 1).Trim()
    }
    
    if ($posAddr -and $posAddr.Length -eq 42) {
        # Save to CONTRACT_ADDRESS.txt (UTF-8, no BOM)
        [System.IO.File]::WriteAllText("CONTRACT_ADDRESS.txt", "$posAddr`n")
        
        # Save to deployment.json
        @{
            posAddress = $posAddr
            timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            network = "localhost:8545"
        } | ConvertTo-Json | Out-File -FilePath "deployment.json" -Force
        
        # Save to frontend config so both instructor and student auto-sync
        $configJson = "{`"contractAddress`":`"$posAddr`",`"deployedAt`":`"$(Get-Date -Format o)`"}"
        [System.IO.File]::WriteAllText("frontend\public\contract-config.json", $configJson)
        
        # Display prominently
        Write-Host ""
        Write-Host "██████████████████████████████████████████████████████████████" -ForegroundColor Magenta
        Write-Host "█                                                            █" -ForegroundColor Magenta
        Write-Host "█  CONTRACT ADDRESS (WRITE ON BOARD):                       █" -ForegroundColor Magenta
        Write-Host "█                                                            █" -ForegroundColor Magenta  
        Write-Host "█  $posAddr  █" -ForegroundColor White -BackgroundColor DarkMagenta
        Write-Host "█                                                            █" -ForegroundColor Magenta
        Write-Host "█  Saved to: CONTRACT_ADDRESS.txt & contract-config.json    █" -ForegroundColor Cyan
        Write-Host "█                                                            █" -ForegroundColor Magenta
        Write-Host "██████████████████████████████████████████████████████████████" -ForegroundColor Magenta
    } 
    else {
        Write-Host "Could not extract contract address. Check deployment output above." -ForegroundColor Red
    }

    # 3. Deploy Beacon Chain Lab
    Write-Host ""
    Write-Host "[3/6] Deploying Beacon Chain Lab..." -ForegroundColor Green
    npm run deploy:beacon-lab
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Beacon Chain Lab deployment failed. Continuing..." -ForegroundColor Yellow
    } else {
        Write-Host "Beacon Chain Lab deployed. beacon-lab-config.json created." -ForegroundColor Green
    }

    # 4. Start Lab API (session, fund requests, wallet tracking) in a new window
    Write-Host ""
    Write-Host "[4/7] Starting Lab API (port 3000)..." -ForegroundColor Green
    $labApiEnv = "INSTRUCTOR_IP=127.0.0.1,::1,$ipAddr"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", `
        "`$env:INSTRUCTOR_IP='127.0.0.1,::1,$ipAddr'; Write-Host 'LAB API' -ForegroundColor Cyan; Write-Host 'Session, fund requests: http://localhost:3000' -ForegroundColor Gray; Set-Location '$labDir'; npm run lab-api" -WorkingDirectory $labDir
    Start-Sleep -Seconds 2

    # 5. Start Lab Terminal (PTY) in a new window
    Write-Host ""
    Write-Host "[5/7] Starting Lab Terminal (port 3002)..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", `
        "Write-Host 'LAB TERMINAL (PTY)' -ForegroundColor Cyan; Write-Host 'WebSocket: ws://localhost:3002' -ForegroundColor Gray; Set-Location '$labDir'; npm run terminal" -WorkingDirectory $labDir
    Start-Sleep -Seconds 2

    # 6. Start ngrok if requested
    $rpcUrl = "http://$($ipAddr):8545"
    if ($UseNgrok) {
        if ($hasNgrok) {
            Write-Host ""
            Write-Host "[6/6] Starting ngrok for remote RPC access..." -ForegroundColor Green
            Start-Process powershell -ArgumentList "-NoExit", "-Command", `
                "Write-Host 'NGROK RPC TUNNEL' -ForegroundColor Cyan; Write-Host 'Copy the HTTPS URL shown below and share with students' -ForegroundColor Yellow; ngrok http 8545"
            Start-Sleep -Seconds 3
            Write-Host "Open the ngrok window to view the HTTPS URL for students." -ForegroundColor Yellow
            $rpcUrl = "<See ngrok window for HTTPS URL>"
        } else {
            Write-Host ""
            Write-Host "[6/7] Ngrok not found. Students will use your local IP for RPC." -ForegroundColor Yellow
            Write-Host "TIP: Install ngrok from https://ngrok.com/download for remote students" -ForegroundColor Cyan
        }
    } else {
        Write-Host ""
        Write-Host "[6/7] Skipping ngrok (use -UseNgrok flag to enable)" -ForegroundColor Gray
        if ($hasNgrok) {
            Write-Host "TIP: Run with -UseNgrok to expose your lab to remote students" -ForegroundColor Cyan
        }
    }

    # 8. Create instructor config and start frontend
    Write-Host ""
    Write-Host "Starting instructor dashboard..." -ForegroundColor Green

    # Create instructor info file
    @{
        role = "instructor"
        contractAddress = $posAddr
        rpcUrl = $rpcUrl
        localIp = $ipAddr
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    } | ConvertTo-Json | Out-File -FilePath "instructor-config.json" -Force

    # Final Instructions
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host "INSTRUCTOR SETUP COMPLETE" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "REMOTE STUDENTS - Open in browser:" -ForegroundColor Magenta
    Write-Host "  http://$($ipAddr):5173" -ForegroundColor Yellow
    Write-Host "  (Web UI + Lab Terminal + CLI access - all in one)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "WRITE ON BOARD FOR STUDENTS:" -ForegroundColor Magenta
    Write-Host "  Lab URL:      http://$($ipAddr):5173" -ForegroundColor Yellow
    Write-Host "  Contract:     $posAddr" -ForegroundColor Yellow
    if ($UseNgrok) {
        Write-Host "  RPC URL: [see ngrok window]" -ForegroundColor Yellow
    } else {
        Write-Host "  RPC URL:     http://$($ipAddr):8545" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Firewall: Allow ports 5173, 8545, 3000, 3002 (if students can't connect)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Alternative (run app locally):" -ForegroundColor Cyan
    Write-Host "  .\start-lab.ps1 -Mode student" -ForegroundColor White
    Write-Host ""
    Write-Host "FILES CREATED:" -ForegroundColor Gray
    Write-Host "  CONTRACT_ADDRESS.txt  - Contract address only" -ForegroundColor Gray
    Write-Host "  deployment.json       - Full deployment details" -ForegroundColor Gray
    Write-Host "  instructor-config.json - Instructor configuration" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Beacon Chain Lab: Sidebar -> Beacon Chain Lab (or ?view=beacon-lab)" -ForegroundColor Cyan
    Write-Host "Lab Terminal: Live view -> Lab Terminal button (CLI, Contract Builder)" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Yellow

    Write-Host "`nOpening Instructor Dashboard in your browser..."
    Start-Process "http://localhost:5173/?mode=instructor"
    npm run web
}

# ============================================================================
# STUDENT MODE
# ============================================================================
function Start-StudentMode {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "   STUDENT MODE - BLOCKCHAIN LEARNER" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    $configPath = "student-config.json"

    # Load previous configuration if exists
    if (Test-Path $configPath) {
        Write-Host "Loading previous configuration..." -ForegroundColor Gray
        try {
            $config = Get-Content $configPath -Raw | ConvertFrom-Json
            if (-not $ContractAddress) { $script:ContractAddress = $config.contractAddress }
            if (-not $RpcUrl) { $script:RpcUrl = $config.rpcUrl }
        } catch {
            Write-Host "Warning: could not read previous config. Continuing..." -ForegroundColor Yellow
        }
    }

    # Prompt for contract address if not provided
    if (-not $ContractAddress) {
        Write-Host ""
        Write-Host "Enter the Contract Address from your instructor (ex: 0x1234...)" -ForegroundColor Yellow
        $script:ContractAddress = Read-Host "Contract Address"
    }

    # Prompt for RPC URL if not provided
    if (-not $RpcUrl) {
        Write-Host ""
        Write-Host "Enter the RPC URL from your instructor." -ForegroundColor Yellow
        Write-Host "Examples:" -ForegroundColor Gray
        Write-Host "  http://INSTRUCTOR_IP:8545" -ForegroundColor Gray
        Write-Host "  https://your-rpc.ngrok-free.app" -ForegroundColor Gray
        $script:RpcUrl = Read-Host "RPC URL"
    }

    # Validate contract address
    if ($ContractAddress.Length -ne 42 -or (-not $ContractAddress.StartsWith("0x"))) {
        Write-Host "Invalid contract address. Must start with 0x and be 42 characters." -ForegroundColor Red
        exit 1
    }

    # Validate RPC URL
    if (-not $RpcUrl.StartsWith("http")) {
        Write-Host "Invalid RPC URL. Must start with http:// or https://" -ForegroundColor Red
        exit 1
    }

    # Save configuration
    @{
        role = "student"
        contractAddress = $ContractAddress
        rpcUrl = $RpcUrl
        timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    } | ConvertTo-Json | Out-File -FilePath $configPath -Force

    # Test connection
    Write-Host ""
    Write-Host "[1/3] Testing connection to instructor blockchain..." -ForegroundColor Green
    try {
        $body = '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
        $response = Invoke-RestMethod -Uri $RpcUrl -Method POST -Body $body -ContentType "application/json" -TimeoutSec 5
        if ($response.result) {
            $blockNum = [Convert]::ToInt32($response.result, 16)
            Write-Host "Connected! Current block: $blockNum" -ForegroundColor Green
        }
    } catch {
        Write-Host "Could not reach instructor RPC. You can still continue and configure inside the app." -ForegroundColor Yellow
    }

    # Set environment variables
    $env:VITE_CONTRACT_ADDRESS = $ContractAddress
    $env:VITE_RPC_URL = $RpcUrl

    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host ""
        Write-Host "[2/3] Installing dependencies..." -ForegroundColor Green
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install dependencies. Please check npm output." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host ""
        Write-Host "[2/3] Dependencies already installed." -ForegroundColor Green
    }

    # Start frontend
    Write-Host ""
    Write-Host "[3/3] Starting Web3 Training Lab..." -ForegroundColor Green

    # Create student setup page that configures localStorage
    $setupHtml = @"
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Student Setup</title>
  <script>
    localStorage.setItem('pos_addr', '$ContractAddress');
    localStorage.setItem('custom_rpc', '$RpcUrl');
    localStorage.setItem('student_mode', 'true');
    window.location.href = 'http://localhost:5173';
  </script>
</head>
<body>
  <h1>Preparing your lab...</h1>
</body>
</html>
"@

    $setupPath = "frontend/public/student-setup.html"
    $setupHtml | Set-Content -Path $setupPath -Encoding UTF8

    Start-Process "http://localhost:5173/student-setup.html"

    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host "STUDENT SETUP COMPLETE" -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Yellow
    Write-Host "Contract: $ContractAddress" -ForegroundColor White
    Write-Host "RPC URL: $RpcUrl" -ForegroundColor White
    Write-Host "==================================================" -ForegroundColor Yellow

    npm run web
}

# ============================================================================
# BEACON LAB ONLY (lightweight: chain + beacon lab + web)
# ============================================================================
function Start-BeaconLabOnly {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "   BEACON CHAIN LAB (standalone)" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan

    $labDir = (Get-Location).Path

    # 1. Start Hardhat Node
    Write-Host ""
    Write-Host "[1/3] Starting blockchain node..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$labDir'; Write-Host 'BLOCKCHAIN NODE - Keep open!' -ForegroundColor Cyan; npm run chain" -WorkingDirectory $labDir

    Write-Host "Waiting for node..." -ForegroundColor Yellow
    $attempt = 0
    while ($attempt -lt 60) {
        Start-Sleep -Seconds 1
        $attempt++
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8545" -Method POST -Body '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' -ContentType "application/json" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($r.Content -match '"result"') {
                Write-Host "Node ready!" -ForegroundColor Green
                break
            }
        } catch { Write-Host "." -NoNewline }
    }
    if ($attempt -ge 60) {
        Write-Host "`nNode failed to start." -ForegroundColor Red
        exit 1
    }
    Start-Sleep -Seconds 2

    # 2. Deploy Beacon Chain Lab
    Write-Host ""
    Write-Host "[2/3] Deploying Beacon Chain Lab..." -ForegroundColor Green
    npm run deploy:beacon-lab
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Deploy failed." -ForegroundColor Red
        exit 1
    }

    # 3. Start frontend
    Write-Host ""
    Write-Host "[3/3] Starting frontend..." -ForegroundColor Green
    Write-Host "Open: http://localhost:5173/?view=beacon-lab" -ForegroundColor Yellow
    Write-Host ""
    Start-Process "http://localhost:5173/?view=beacon-lab"
    npm run web
}

# ============================================================================
# MAIN
# ============================================================================
Write-Host ""
Write-Host "==================================================" -ForegroundColor White
Write-Host "   WEB3 CLASSROOM LAB" -ForegroundColor White
Write-Host "==================================================" -ForegroundColor White

if ($Mode -eq "instructor") {
    Start-InstructorMode
} elseif ($Mode -eq "reset") {
    Start-ResetMode
} elseif ($Mode -eq "beacon-lab") {
    Start-BeaconLabOnly
} else {
    Start-StudentMode
}
