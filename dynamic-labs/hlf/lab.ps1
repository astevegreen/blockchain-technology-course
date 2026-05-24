<#
Hyperledger Fabric Standalone Lab Launcher (PowerShell)

Usage:
  .\lab.ps1 doctor
  .\lab.ps1 bootstrap
  .\lab.ps1 up
  .\lab.ps1 health
  .\lab.ps1 deploy
  .\lab.ps1 enter org1|org2
  .\lab.ps1 watch logs|blocks|state
  .\lab.ps1 web-ui
  .\lab.ps1 down
  .\lab.ps1 reset
  .\lab.ps1 status
  .\lab.ps1 invoke <args...>
  .\lab.ps1 query <args...>

Notes:
- Full functionality (bootstrap/up/enter/watch blocks/state) is best in WSL or Git Bash.
- This PowerShell wrapper supports the most common workflow and will use `bash` when available.
#>

param(
  [Parameter(Position=0)][string]$Command = "",
  [Parameter(Position=1)][string]$Arg1 = "",
  [Parameter(Position=2)][string]$Arg2 = "",
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$Rest = @()
)

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$LabSh = Join-Path $Here "lab.sh"

function Die($msg) {
  Write-Error "[hlf] $msg"
  exit 1
}

function Info($msg) {
  Write-Host "[hlf] $msg"
}

function Have($name) {
  return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function RunBash($cmd) {
  if (Have "bash") {
    & bash -lc $cmd
  } else {
    Die "bash not found. Install Git Bash or use WSL for full functionality."
  }
}

function BashQuote {
  param([string]$s)
  $replacement = "'" + '"' + "'" + '"' + "'"
  return "'" + ($s -replace "'", $replacement) + "'"
}

function RunLabSh {
  param([string]$cmd, [string[]]$labArgs)
  $parts = @()
  $parts += "cd $(BashQuote $Here)"
  $parts += "&&"
  $parts += (BashQuote $LabSh)
  $parts += $cmd
  foreach ($a in $labArgs) {
    if ($a -ne "") { $parts += (BashQuote $a) }
  }
  RunBash ($parts -join " ")
}

if (-not $Command) {
  Write-Host "Run: .\lab.ps1 doctor|bootstrap|up|health|deploy|enter|watch|web-ui|down|reset|status|invoke|query"
} elseif ($Command -eq "doctor") {
  if (-not (Have "docker")) { Die "docker not found in PATH." }
  try { docker info | Out-Null } catch { Die "Docker daemon not reachable. Start Docker Desktop." }
  Info "OK"
} elseif ($Command -eq "bootstrap") {
  Info "Running bootstrap via bash..."
  RunLabSh "bootstrap" @()
} elseif ($Command -eq "up") {
  Info "Starting network via bash..."
  RunLabSh "up" @()
} elseif ($Command -eq "health") {
  Info "Checking network health via bash..."
  RunLabSh "health" @()
} elseif ($Command -eq "deploy") {
  Info "Deploying chaincode via bash..."
  RunLabSh "deploy" @()
} elseif ($Command -eq "down") {
  Info "Tearing down via bash..."
  RunLabSh "down" @()
} elseif ($Command -eq "reset") {
  Info "Reset via bash..."
  RunLabSh "reset" @()
} elseif ($Command -eq "enter") {
  if ($Arg1 -ne "org1" -and $Arg1 -ne "org2") { Die "enter expects org1 or org2" }
  Info "Entering tools shell ($Arg1) via bash..."
  RunLabSh "enter" @($Arg1)
} elseif ($Command -eq "watch") {
  if ($Arg1 -eq "") { Die "watch expects logs|blocks|state" }
  Info "Starting watcher via bash..."
  RunLabSh "watch" @($Arg1)
} elseif ($Command -eq "web-ui") {
  Info "Launching web UI via bash..."
  RunLabSh "web-ui" @()
} elseif ($Command -eq "status") {
  Info "Checking status via bash..."
  RunLabSh "status" @()
} elseif ($Command -eq "invoke") {
  $invokeArgs = @()
  if ($Arg1 -ne "") { $invokeArgs += $Arg1 }
  if ($Arg2 -ne "") { $invokeArgs += $Arg2 }
  if ($Rest.Count -gt 0) { $invokeArgs += $Rest }
  Info "Invoking chaincode via bash..."
  RunLabSh "invoke" $invokeArgs
} elseif ($Command -eq "query") {
  $queryArgs = @()
  if ($Arg1 -ne "") { $queryArgs += $Arg1 }
  if ($Arg2 -ne "") { $queryArgs += $Arg2 }
  if ($Rest.Count -gt 0) { $queryArgs += $Rest }
  Info "Querying chaincode via bash..."
  RunLabSh "query" $queryArgs
} else {
  Die "Unknown command: $Command"
}
