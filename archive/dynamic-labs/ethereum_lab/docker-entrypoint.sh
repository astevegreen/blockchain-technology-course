#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ETHEREUM IMMERSIVE TRAINER                             ║"
echo "║     Interactive Blockchain Learning Environment            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Default values
MODE="${MODE:-instructor}"
RPC_PORT="${RPC_PORT:-8545}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo -e "Mode: ${BLUE}$MODE${NC}"
echo ""

# Graceful shutdown handler
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$NGINX_PID" ]; then
        kill $NGINX_PID 2>/dev/null || true
    fi
    if [ ! -z "$HARDHAT_PID" ]; then
        kill $HARDHAT_PID 2>/dev/null || true
    fi
    if [ ! -z "$TERMINAL_PID" ]; then
        kill $TERMINAL_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}
trap cleanup SIGTERM SIGINT

seed_student_home_if_needed() {
    local home_dir="${HOME:-/home/student}"
    local seed_dir="${STUDENT_HOME_SEED_PATH:-/opt/student-home-seed}"
    local marker="${home_dir}/.student-home-seeded"
    local owner_uid="${STUDENT_HOME_OWNER_UID:-1000}"
    local owner_gid="${STUDENT_HOME_OWNER_GID:-1000}"

    if [ ! -d "$seed_dir" ]; then
        return 0
    fi

    mkdir -p "$home_dir"

    if [ ! -e "$marker" ]; then
        cp -an "${seed_dir}/." "${home_dir}/"
        touch "$marker"
    fi

    chown "${owner_uid}:${owner_gid}" "$home_dir" "$marker" 2>/dev/null || true
}

# ============================================
# INSTRUCTOR MODE
# Runs blockchain node + deploys contracts + serves frontend
# ============================================
if [ "$MODE" = "instructor" ]; then
    LAB_TERMINAL_ENABLED="${LAB_TERMINAL_ENABLED:-1}"
    NGINX_ENABLED="${NGINX_ENABLED:-1}"
    echo -e "${GREEN}🎓 Starting INSTRUCTOR mode...${NC}"
    echo "   - Blockchain node will run on port $RPC_PORT"
    echo "   - Frontend will run on port $FRONTEND_PORT"
    [ "$NGINX_ENABLED" = "1" ] || [ "$NGINX_ENABLED" = "true" ] && echo "   - Nginx will route all traffic on port 8080"
    echo ""
    
    # Ensure contracts directory exists
    mkdir -p /app/contracts/student
    
    # Start Hardhat node in background.
    # IMPORTANT: redirect stdout to /dev/null. Hardhat logs EVERY JSON-RPC call (~hundreds
    # of lines/sec under student polling); that stream is ingested by the shared dockerd
    # log driver and was burning host CPU across ALL labs. stderr is kept for real errors.
    echo -e "${BLUE}⛓️  Starting Hardhat blockchain node...${NC}"
    npx hardhat node --hostname 0.0.0.0 --port $RPC_PORT >/dev/null &
    HARDHAT_PID=$!
    
    # Wait for node to be ready
    echo "   Waiting for blockchain node to start..."
    # The packaged VM can be CPU-constrained, so allow extra time for the
    # first JSON-RPC check before declaring startup failure.
    for i in $(seq 1 60); do
        if curl -s -X POST http://localhost:$RPC_PORT \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓ Blockchain node is ready!${NC}"
            break
        fi
        if [ $i -eq 60 ]; then
            echo -e "   ${RED}✗ Failed to start blockchain node!${NC}"
            exit 1
        fi
        sleep 2
    done
    
    # Brief pause to ensure node is fully ready for deployments
    sleep 2

    # Make the class-bank account effectively inexhaustible for classroom use.
    # The top-off API still caps each request; this only prevents repeated
    # legitimate top-offs from draining the Hardhat default 10,000 ETH account.
    echo ""
    echo -e "${BLUE}🏦 Funding class faucet bank...${NC}"
    export FAUCET_RPC_URL="${FAUCET_RPC_URL:-http://127.0.0.1:$RPC_PORT}"
    if ! node scripts/ensure-faucet-balance.js; then
        echo -e "   ${RED}✗ Failed to fund class faucet bank${NC}"
        exit 1
    fi
    
    # Deploy PoS contracts (must succeed or container exits)
    echo ""
    echo -e "${BLUE}📜 Deploying PoS Simulator...${NC}"
    if ! npx hardhat run --no-compile scripts/deploy.js --network localhost; then
        echo ""
        echo -e "${RED}✗ Contract deployment failed!${NC}"
        echo "  If you see 'Transaction reverted' or 'require(false)', try:"
        echo "  1. docker-compose down -v   (removes persisted data)"
        echo "  2. docker-compose up --build"
        exit 1
    fi
    
    # Derive + fund the configured student pool (lane-service reads
    # this JSON via HTTP and injects per-lane ASSIGNED_ADDRESS).
    echo ""
    export POOL_SIZE="${POOL_SIZE:-${ETHEREUM_STUDENT_CAPACITY:-${MAX_STUDENT_CAPACITY:-20}}}"
    echo -e "${BLUE}👥 Setting up student address pool...${NC}"
    echo "   - Pool size: ${POOL_SIZE}"
    if ! npx hardhat run --no-compile scripts/setup-student-pool.js --network localhost; then
        echo -e "   ${YELLOW}⚠ Student pool setup failed (lane-service claims will fail)${NC}"
    fi

    # Deploy Beacon Chain Lab (optional, set DEPLOY_BEACON_LAB=1 to enable)
    if [ "${DEPLOY_BEACON_LAB}" = "1" ]; then
        echo ""
        echo -e "${BLUE}⛓ Deploying Beacon Chain Lab...${NC}"
        if npx hardhat run --no-compile scripts/deploy-beacon-lab.js --network localhost; then
            echo -e "   ${GREEN}✓ Beacon Chain Lab deployed${NC}"
            if [ -f "/app/frontend/public/beacon-lab-config.json" ]; then
                cp /app/frontend/public/beacon-lab-config.json /app/frontend/dist/beacon-lab-config.json
                echo -e "   ${GREEN}✓ beacon-lab-config.json copied to frontend${NC}"
            fi
        else
            echo -e "   ${YELLOW}⚠ Beacon Chain Lab deployment failed${NC}"
        fi
    fi

    TOKENIZATION_NFT_ADDRESS=""
    TOKENIZATION_SALE_ADDRESS=""
    TOKENIZATION_MARKETPLACE_ADDRESS=""
    ARCADE_TOKEN_ADDRESS=""
    ARCADE_VENDOR_ADDRESS=""
    ARCADE_VAULT_ADDRESS=""
    ARCADE_TOKEN_PRICE_WEI=""
    ARCADE_TOKEN_PRICE_ETH=""
    ARCADE_TREASURY_ADDRESS=""
    ARCADE_PLAY_COST=""
    ENTROPY_LOTTERY_ADDRESS=""
    THOUSAND_ETH_DOUBLER_ADDRESS=""
    VULNERABLE_BANK_VAULT_ADDRESS=""
    HONEYPOT_TOKEN_ADDRESS=""
    APPROVAL_DRAINER_ADDRESS=""
    FAKE_AIRDROP_CLAIMER_ADDRESS=""
    TIMELOCK_RUG_VAULT_ADDRESS=""
    TOKENIZATION_UPDATED_AT=""
    echo ""
    echo -e "${BLUE}🪙 Deploying Tokenization Lab contracts...${NC}"
    if npx hardhat run --no-compile scripts/deploy-tokenization-contracts.js --network localhost; then
        if [ -f "/app/frontend/public/labs/ethereum_lab/tokenization-config.json" ]; then
            TOKENIZATION_NFT_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').nftAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            TOKENIZATION_SALE_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').saleAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            TOKENIZATION_MARKETPLACE_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').marketplaceAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_TOKEN_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeTokenAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_VENDOR_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeVendorAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_VAULT_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeVaultAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_TOKEN_PRICE_WEI=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeTokenPriceWei||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_TOKEN_PRICE_ETH=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeTokenPriceEth||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_TREASURY_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadeTreasuryAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            ARCADE_PLAY_COST=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').arcadePlayCost||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            TOKENIZATION_UPDATED_AT=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/tokenization-config.json').updatedAt||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            echo -e "   ${GREEN}✓ Tokenization Lab contracts deployed${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠ Tokenization Lab deployment failed${NC}"
    fi

    # Deploy intentionally flawed DeFi contracts for discovery/exploitation labs.
    # This must run before the Beacon conductor snapshots the chain state.
    if [ "${DEPLOY_DEFI_RISK_CONTRACTS:-1}" != "0" ]; then
        echo ""
        echo -e "${BLUE}🧪 Deploying DeFi Risk Garden contracts...${NC}"
        if npx hardhat run --no-compile scripts/deploy-defi-risk-contracts.js --network localhost; then
            if [ -f "/app/frontend/public/labs/ethereum_lab/defi-risk-config.json" ]; then
                ENTROPY_LOTTERY_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').entropyLotteryAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                THOUSAND_ETH_DOUBLER_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').thousandEthDoublerAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                VULNERABLE_BANK_VAULT_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').vulnerableBankVaultAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                HONEYPOT_TOKEN_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').honeypotTokenAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                APPROVAL_DRAINER_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').approvalDrainerAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                FAKE_AIRDROP_CLAIMER_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').fakeAirdropClaimerAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
                TIMELOCK_RUG_VAULT_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/labs/ethereum_lab/defi-risk-config.json').timelockRugVaultAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
            fi
            echo -e "   ${GREEN}✓ DeFi Risk Garden contracts deployed${NC}"
        else
            echo -e "   ${YELLOW}⚠ DeFi Risk Garden deployment failed${NC}"
        fi
    fi

    # Start the self-running PoS conductor AFTER the Beacon, Tokenization, and
    # DeFi risk contracts are deployed. The conductor takes an evm_snapshot at
    # startup and reverts to it on every prune; if it snapshots before lab
    # contracts deploy, later exercises call codeless addresses.
    # Defaults ON whenever the Beacon lab is deployed; set BEACON_CONDUCTOR=0 to disable.
    if [ "${DEPLOY_BEACON_LAB}" = "1" ] && [ "${BEACON_CONDUCTOR:-1}" != "0" ] && [ -f "/app/frontend/public/beacon-lab-config.json" ]; then
        echo -e "${BLUE}🤖 Starting Beacon conductor...${NC}"
        BEACON_BLOCK_MS="${BEACON_BLOCK_MS:-6000}" node scripts/beacon-conductor.js &
        BEACON_CONDUCTOR_PID=$!
        echo -e "   ${GREEN}✓ Beacon conductor running (pid ${BEACON_CONDUCTOR_PID})${NC}"
    fi

    # Start Lab Terminal (PTY) in background unless disabled (LAB_TERMINAL_ENABLED=0 for students-run-locally)
    if [ "$LAB_TERMINAL_ENABLED" = "1" ] || [ "$LAB_TERMINAL_ENABLED" = "true" ]; then
        echo ""
        echo -e "${BLUE}🖥️  Starting Lab Terminal (ports 3002, 3003, 3004)...${NC}"
        node server/terminal-server.js &
        TERMINAL_PID=$!
        sleep 1
        echo -e "   ${GREEN}✓ Lab Terminal running${NC}"
    else
        echo ""
        echo -e "${YELLOW}Lab Terminal disabled (LAB_TERMINAL_ENABLED=0). Students run terminal locally.${NC}"
    fi
    
    # Read and export contract address
    BEACON_LAB_ADDRESS=""
    if [ -f "/app/frontend/public/beacon-lab-config.json" ]; then
        BEACON_LAB_ADDRESS=$(node -e "try{console.log(require('/app/frontend/public/beacon-lab-config.json').contractAddress||'')}catch(e){console.log('')}" 2>/dev/null || echo "")
    fi

    if [ -f "CONTRACT_ADDRESS.txt" ]; then
        CONTRACT_ADDRESS=$(head -1 CONTRACT_ADDRESS.txt | tr -d '\r\n')
        export CONTRACT_ADDRESS
        
        # Save to web-accessible location for auto-configuration
        mkdir -p /app/frontend/dist/api
        
        # Get container/host IP for external access hints
        CONTAINER_IP=$(hostname -i 2>/dev/null || echo "localhost")
        
        # Create config JSON
        # Browser RPC is write-filtered. Reads must use /chain-state, /beacon-state,
        # or /marketplace-state; /rpc is intentionally unavailable to students.
        # RPC_URL_PUBLIC overrides (e.g. https://host/rpc-write)
        if [ "$NGINX_ENABLED" = "1" ] || [ "$NGINX_ENABLED" = "true" ]; then
            RPC_FOR_CONFIG="${RPC_URL_PUBLIC:-/rpc-write}"
        else
            RPC_FOR_CONFIG="${RPC_URL_PUBLIC:-/rpc-write}"
        fi
        LAB_TERMINAL_JSON="false"
        [ "$LAB_TERMINAL_ENABLED" = "1" ] || [ "$LAB_TERMINAL_ENABLED" = "true" ] && LAB_TERMINAL_JSON="true"
        if [ -n "$BEACON_LAB_ADDRESS" ]; then
        cat > /app/frontend/dist/api/config.json << EOF
{
  "contractAddress": "$CONTRACT_ADDRESS",
  "rpcUrl": "$RPC_FOR_CONFIG",
  "mode": "instructor",
  "startTime": "$(date -Iseconds)",
  "beaconLabContractAddress": "$BEACON_LAB_ADDRESS",
  "tokenizationNftAddress": "$TOKENIZATION_NFT_ADDRESS",
  "tokenizationSaleAddress": "$TOKENIZATION_SALE_ADDRESS",
  "tokenizationMarketplaceAddress": "$TOKENIZATION_MARKETPLACE_ADDRESS",
  "arcadeTokenAddress": "$ARCADE_TOKEN_ADDRESS",
  "arcadeVendorAddress": "$ARCADE_VENDOR_ADDRESS",
  "arcadeVaultAddress": "$ARCADE_VAULT_ADDRESS",
  "arcadeTokenPriceWei": "$ARCADE_TOKEN_PRICE_WEI",
  "arcadeTokenPriceEth": "$ARCADE_TOKEN_PRICE_ETH",
  "arcadeTreasuryAddress": "$ARCADE_TREASURY_ADDRESS",
  "arcadePlayCost": "$ARCADE_PLAY_COST",
  "entropyLotteryAddress": "$ENTROPY_LOTTERY_ADDRESS",
  "thousandEthDoublerAddress": "$THOUSAND_ETH_DOUBLER_ADDRESS",
  "vulnerableBankVaultAddress": "$VULNERABLE_BANK_VAULT_ADDRESS",
  "honeypotTokenAddress": "$HONEYPOT_TOKEN_ADDRESS",
  "approvalDrainerAddress": "$APPROVAL_DRAINER_ADDRESS",
  "fakeAirdropClaimerAddress": "$FAKE_AIRDROP_CLAIMER_ADDRESS",
  "timelockRugVaultAddress": "$TIMELOCK_RUG_VAULT_ADDRESS",
  "tokenizationUpdatedAt": "$TOKENIZATION_UPDATED_AT",
  "labTerminalEnabled": $LAB_TERMINAL_JSON
}
EOF
        else
        cat > /app/frontend/dist/api/config.json << EOF
{
  "contractAddress": "$CONTRACT_ADDRESS",
  "rpcUrl": "$RPC_FOR_CONFIG",
  "mode": "instructor",
  "startTime": "$(date -Iseconds)",
  "tokenizationNftAddress": "$TOKENIZATION_NFT_ADDRESS",
  "tokenizationSaleAddress": "$TOKENIZATION_SALE_ADDRESS",
  "tokenizationMarketplaceAddress": "$TOKENIZATION_MARKETPLACE_ADDRESS",
  "arcadeTokenAddress": "$ARCADE_TOKEN_ADDRESS",
  "arcadeVendorAddress": "$ARCADE_VENDOR_ADDRESS",
  "arcadeVaultAddress": "$ARCADE_VAULT_ADDRESS",
  "arcadeTokenPriceWei": "$ARCADE_TOKEN_PRICE_WEI",
  "arcadeTokenPriceEth": "$ARCADE_TOKEN_PRICE_ETH",
  "arcadeTreasuryAddress": "$ARCADE_TREASURY_ADDRESS",
  "arcadePlayCost": "$ARCADE_PLAY_COST",
  "entropyLotteryAddress": "$ENTROPY_LOTTERY_ADDRESS",
  "thousandEthDoublerAddress": "$THOUSAND_ETH_DOUBLER_ADDRESS",
  "vulnerableBankVaultAddress": "$VULNERABLE_BANK_VAULT_ADDRESS",
  "honeypotTokenAddress": "$HONEYPOT_TOKEN_ADDRESS",
  "approvalDrainerAddress": "$APPROVAL_DRAINER_ADDRESS",
  "fakeAirdropClaimerAddress": "$FAKE_AIRDROP_CLAIMER_ADDRESS",
  "timelockRugVaultAddress": "$TIMELOCK_RUG_VAULT_ADDRESS",
  "tokenizationUpdatedAt": "$TOKENIZATION_UPDATED_AT",
  "labTerminalEnabled": $LAB_TERMINAL_JSON
}
EOF
        fi
        echo "$CONTRACT_ADDRESS" > /app/frontend/dist/contract-address.txt
        
        echo -e "   ${GREEN}✓ Contract deployed!${NC}"
    else
        echo -e "   ${YELLOW}⚠ Warning: Could not find contract address file${NC}"
    fi
    
    # Start frontend server (with Lab API for session/fund-requests)
    echo ""
    echo -e "${BLUE}🌐 Starting frontend server (with Lab API)...${NC}"
    FRONTEND_PORT=$FRONTEND_PORT node /app/server/frontend-server.js &
    FRONTEND_PID=$!
    
    # Wait a moment for frontend to start
    sleep 2
    
    # Start nginx (in-container router) when NGINX_ENABLED=1
    if [ "$NGINX_ENABLED" = "1" ] || [ "$NGINX_ENABLED" = "true" ]; then
        echo ""
        echo -e "${BLUE}🔀 Starting nginx (port 8080 → frontend, /rpc-write, /ws/terminal)...${NC}"
        nginx -c /etc/nginx/nginx-internal.conf &
        NGINX_PID=$!
        sleep 1
        echo -e "   ${GREEN}✓ Nginx running on port 8080${NC}"
    fi
    
    # Print success banner
    echo ""
    HTTP_PORT="8080"
    [ "$NGINX_ENABLED" != "1" ] && [ "$NGINX_ENABLED" != "true" ] && HTTP_PORT="$FRONTEND_PORT"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo -e "║  ${GREEN}✓ INSTRUCTOR NODE IS RUNNING${NC}                                ║"
    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║                                                                ║"
    echo "║  LOCAL ACCESS:                                                 ║"
    if [ "$NGINX_ENABLED" = "1" ] || [ "$NGINX_ENABLED" = "true" ]; then
    echo "║    All-in-one:    http://localhost:8080 (frontend, write RPC, terminal) ║"
    echo "║    Direct:        http://localhost:$FRONTEND_PORT (frontend), localhost:$RPC_PORT (debug RPC)  ║"
    else
    echo "║    Frontend:      http://localhost:$FRONTEND_PORT                       ║"
    echo "║    Blockchain:    http://localhost:$RPC_PORT                        ║"
    fi
    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║                                                                ║"
    echo "║  CONTRACT ADDRESS:                                             ║"
    echo "║    $CONTRACT_ADDRESS                           ║"
    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║                                                                ║"
    echo "║  📋 SHARE WITH STUDENTS:                                       ║"
    echo "║    1. Find your IP: hostname -I (Linux) or ipconfig (Windows)  ║"
    if [ "$NGINX_ENABLED" = "1" ] || [ "$NGINX_ENABLED" = "true" ]; then
    echo "║    2. Share: http://<YOUR-IP>:8080 (single URL for everything)  ║"
    echo "║       - Write RPC: http://<YOUR-IP>:8080/rpc-write                 ║"
    else
    echo "║    2. Share:                                                   ║"
    echo "║       - Frontend: http://<YOUR-IP>:$FRONTEND_PORT                       ║"
    echo "║       - RPC URL:  http://<YOUR-IP>:$RPC_PORT                        ║"
    fi
    echo "║       - Contract: $CONTRACT_ADDRESS            ║"
    echo "║                                                                ║"
    echo "║  📄 Auto-config: http://localhost:$HTTP_PORT/api/config.json         ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
# ============================================
# STUDENT MODE  
# Only serves frontend, connects to instructor's blockchain
# ============================================
elif [ "$MODE" = "student" ]; then
    echo -e "${GREEN}📚 Starting STUDENT mode...${NC}"

    HOME="${HOME:-/home/student}"
    USER="${USER:-student}"
    SHELL="${SHELL:-/bin/bash}"
    STUDENT_HOME_OWNER_UID="${STUDENT_HOME_OWNER_UID:-1000}"
    STUDENT_HOME_OWNER_GID="${STUDENT_HOME_OWNER_GID:-1000}"
    CONTRACT_ADDRESS="${CONTRACT_ADDRESS:-}"
    BEACON_LAB_ADDRESS="${BEACON_LAB_ADDRESS:-}"
    TOKENIZATION_NFT_ADDRESS="${TOKENIZATION_NFT_ADDRESS:-}"
    TOKENIZATION_SALE_ADDRESS="${TOKENIZATION_SALE_ADDRESS:-}"
    TOKENIZATION_MARKETPLACE_ADDRESS="${TOKENIZATION_MARKETPLACE_ADDRESS:-}"
    ARCADE_TOKEN_ADDRESS="${ARCADE_TOKEN_ADDRESS:-}"
    ARCADE_VENDOR_ADDRESS="${ARCADE_VENDOR_ADDRESS:-}"
    ARCADE_VAULT_ADDRESS="${ARCADE_VAULT_ADDRESS:-}"
    ARCADE_TOKEN_PRICE_WEI="${ARCADE_TOKEN_PRICE_WEI:-}"
    ARCADE_TOKEN_PRICE_ETH="${ARCADE_TOKEN_PRICE_ETH:-}"
    ARCADE_TREASURY_ADDRESS="${ARCADE_TREASURY_ADDRESS:-}"
    ARCADE_PLAY_COST="${ARCADE_PLAY_COST:-}"
    ENTROPY_LOTTERY_ADDRESS="${ENTROPY_LOTTERY_ADDRESS:-}"
    THOUSAND_ETH_DOUBLER_ADDRESS="${THOUSAND_ETH_DOUBLER_ADDRESS:-}"
    VULNERABLE_BANK_VAULT_ADDRESS="${VULNERABLE_BANK_VAULT_ADDRESS:-}"
    HONEYPOT_TOKEN_ADDRESS="${HONEYPOT_TOKEN_ADDRESS:-}"
    APPROVAL_DRAINER_ADDRESS="${APPROVAL_DRAINER_ADDRESS:-}"
    FAKE_AIRDROP_CLAIMER_ADDRESS="${FAKE_AIRDROP_CLAIMER_ADDRESS:-}"
    TIMELOCK_RUG_VAULT_ADDRESS="${TIMELOCK_RUG_VAULT_ADDRESS:-}"
    TOKENIZATION_UPDATED_AT="${TOKENIZATION_UPDATED_AT:-}"
    TERMINAL_RPC_URL="${TERMINAL_RPC_URL:-${INSTRUCTOR_RPC_URL:-}}"
    # Managed student lanes default the in-browser terminal OFF. It spawns a second
    # Node process (terminal-server.js + node-pty) per lane AND exposes
    # `hardhat console --network instructor` straight to the SHARED node — both of
    # which crush the host at 25-30 concurrent students. lane-service sets this to 0;
    # set LAB_TERMINAL_ENABLED=1 to re-enable (e.g. a single standalone student box).
    LAB_TERMINAL_ENABLED="${LAB_TERMINAL_ENABLED:-0}"
    seed_student_home_if_needed
    
    # Check for required instructor connection info
    if [ -z "$INSTRUCTOR_RPC_URL" ]; then
        echo ""
        echo -e "${YELLOW}⚠️  INSTRUCTOR_RPC_URL not set!${NC}"
        echo "   Students need to connect to instructor's blockchain."
        echo ""
        echo "   Set environment variable:"
        echo "   INSTRUCTOR_RPC_URL=http://<instructor-ip>:8545"
        echo ""
        INSTRUCTOR_RPC_URL="http://localhost:8545"
    fi
    
    echo "   - Connecting to: $INSTRUCTOR_RPC_URL"
    echo "   - Frontend will run on port $FRONTEND_PORT"
    echo ""
    
    # Start Lab Terminal (PTY) only when explicitly enabled. Disabled by default for
    # managed student lanes (see note above): keeps each lane to a single Node process
    # and blocks direct `hardhat console --network instructor` access to the shared node.
    if [ "$LAB_TERMINAL_ENABLED" = "1" ] || [ "$LAB_TERMINAL_ENABLED" = "true" ]; then
    echo -e "${BLUE}🖥️  Starting Lab Terminal (ports 3002, 3003, 3004)...${NC}"
    TERMINAL_PORTS="${TERMINAL_PORTS:-3002,3003,3004}" \
    TERMINAL_CWD="${TERMINAL_CWD:-/home/student/workspace}" \
    HOME="${HOME}" \
    USER="${USER}" \
    SHELL="${SHELL}" \
    TERMINAL_UID="${TERMINAL_UID:-1000}" \
    TERMINAL_GID="${TERMINAL_GID:-1000}" \
    PATH="/home/student/workspace/node_modules/.bin:/app/node_modules/.bin:${PATH}" \
    node server/terminal-server.js &
    TERMINAL_PID=$!
    sleep 1
    echo -e "   ${GREEN}✓ Lab Terminal running (students can use terminal from browser)${NC}"
    else
        echo -e "${YELLOW}🚫 Lab Terminal disabled for this lane (LAB_TERMINAL_ENABLED=0) — GUI-only${NC}"
    fi
    echo ""
    
    # Browsers always use this lane's write-filtered proxy. The proxy itself
    # targets $INSTRUCTOR_RPC_URL server-side when running in standalone
    # student mode; platform lanes override with /rpc-write as well.
    RPC_FOR_CONFIG="${RPC_URL_PUBLIC:-/rpc-write}"
    # Managed student lanes get contract metadata injected by lane-service.
    # Standalone student containers can still pull the deploy config from
    # an explicit instructor HTTP endpoint when provided.
    if [ -n "${INSTRUCTOR_HTTP_URL:-}" ] && { [ -z "$CONTRACT_ADDRESS" ] || [ -z "$TIMELOCK_RUG_VAULT_ADDRESS" ]; }; then
        for i in $(seq 1 30); do
            CFG=$(curl -fsS "${INSTRUCTOR_HTTP_URL%/}/api/config.json" 2>/dev/null || true)
            if [ -n "$CFG" ]; then
                CONTRACT_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).contractAddress||'')}catch(e){}})")
                BEACON_LAB_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).beaconLabContractAddress||'')}catch(e){}})")
                TOKENIZATION_NFT_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).tokenizationNftAddress||'')}catch(e){}})")
                TOKENIZATION_SALE_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).tokenizationSaleAddress||'')}catch(e){}})")
                TOKENIZATION_MARKETPLACE_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).tokenizationMarketplaceAddress||'')}catch(e){}})")
                ARCADE_TOKEN_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeTokenAddress||'')}catch(e){}})")
                ARCADE_VENDOR_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeVendorAddress||'')}catch(e){}})")
                ARCADE_VAULT_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeVaultAddress||'')}catch(e){}})")
                ARCADE_TOKEN_PRICE_WEI=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeTokenPriceWei||'')}catch(e){}})")
                ARCADE_TOKEN_PRICE_ETH=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeTokenPriceEth||'')}catch(e){}})")
                ARCADE_TREASURY_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadeTreasuryAddress||'')}catch(e){}})")
                ARCADE_PLAY_COST=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).arcadePlayCost||'')}catch(e){}})")
                ENTROPY_LOTTERY_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).entropyLotteryAddress||'')}catch(e){}})")
                THOUSAND_ETH_DOUBLER_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).thousandEthDoublerAddress||'')}catch(e){}})")
                VULNERABLE_BANK_VAULT_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).vulnerableBankVaultAddress||'')}catch(e){}})")
                HONEYPOT_TOKEN_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).honeypotTokenAddress||'')}catch(e){}})")
                APPROVAL_DRAINER_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).approvalDrainerAddress||'')}catch(e){}})")
                FAKE_AIRDROP_CLAIMER_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).fakeAirdropClaimerAddress||'')}catch(e){}})")
                TIMELOCK_RUG_VAULT_ADDRESS=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).timelockRugVaultAddress||'')}catch(e){}})")
                TOKENIZATION_UPDATED_AT=$(echo "$CFG" | node -e "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{try{console.log(JSON.parse(s).tokenizationUpdatedAt||'')}catch(e){}})")
                [ -n "$CONTRACT_ADDRESS" ] && break
            fi
            sleep 1
        done
    fi
    echo "   - Contract: ${CONTRACT_ADDRESS:-<unresolved>}"

    # Create config for student to connect to instructor
    mkdir -p /app/frontend/dist/api
    LAB_TERMINAL_JSON="false"
    [ "$LAB_TERMINAL_ENABLED" = "1" ] || [ "$LAB_TERMINAL_ENABLED" = "true" ] && LAB_TERMINAL_JSON="true"
    cat > /app/frontend/dist/api/config.json << EOF
{
  "rpcUrl": "$RPC_FOR_CONFIG",
  "terminalRpcUrl": "$TERMINAL_RPC_URL",
  "contractAddress": "$CONTRACT_ADDRESS",
  "beaconLabContractAddress": "$BEACON_LAB_ADDRESS",
  "tokenizationNftAddress": "$TOKENIZATION_NFT_ADDRESS",
  "tokenizationSaleAddress": "$TOKENIZATION_SALE_ADDRESS",
  "tokenizationMarketplaceAddress": "$TOKENIZATION_MARKETPLACE_ADDRESS",
  "arcadeTokenAddress": "$ARCADE_TOKEN_ADDRESS",
  "arcadeVendorAddress": "$ARCADE_VENDOR_ADDRESS",
  "arcadeVaultAddress": "$ARCADE_VAULT_ADDRESS",
  "arcadeTokenPriceWei": "$ARCADE_TOKEN_PRICE_WEI",
  "arcadeTokenPriceEth": "$ARCADE_TOKEN_PRICE_ETH",
  "arcadeTreasuryAddress": "$ARCADE_TREASURY_ADDRESS",
  "arcadePlayCost": "$ARCADE_PLAY_COST",
  "entropyLotteryAddress": "$ENTROPY_LOTTERY_ADDRESS",
  "thousandEthDoublerAddress": "$THOUSAND_ETH_DOUBLER_ADDRESS",
  "vulnerableBankVaultAddress": "$VULNERABLE_BANK_VAULT_ADDRESS",
  "honeypotTokenAddress": "$HONEYPOT_TOKEN_ADDRESS",
  "approvalDrainerAddress": "$APPROVAL_DRAINER_ADDRESS",
  "fakeAirdropClaimerAddress": "$FAKE_AIRDROP_CLAIMER_ADDRESS",
  "timelockRugVaultAddress": "$TIMELOCK_RUG_VAULT_ADDRESS",
  "tokenizationUpdatedAt": "$TOKENIZATION_UPDATED_AT",
  "mode": "student",
  "station": "${STATION:-}",
  "assignedAddress": "${ASSIGNED_ADDRESS:-}",
  "assignedPrivateKey": "${ASSIGNED_PRIVATE_KEY:-}",
  "startTime": "$(date -Iseconds)",
  "labTerminalEnabled": $LAB_TERMINAL_JSON
}
EOF
    
    # Start frontend server (includes Lab Terminal WebSocket proxy at /ws/terminal)
    echo -e "${BLUE}🌐 Starting frontend server...${NC}"
    FRONTEND_PORT=$FRONTEND_PORT node /app/server/frontend-server.js &
    FRONTEND_PID=$!
    
    sleep 2
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo -e "║  ${GREEN}✓ STUDENT CLIENT IS RUNNING${NC}                               ║"
    echo "║                                                            ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    echo "║  Frontend:        http://localhost:$FRONTEND_PORT                  ║"
    echo "║  Lab Terminal:    ports 3002, 3003, 3004 (browser shell)   ║"
    echo "║  Instructor RPC:  $INSTRUCTOR_RPC_URL"
    echo "║                                                            ║"
    echo "║  Open browser to: http://localhost:$FRONTEND_PORT                  ║"
    echo "║  Lab Terminal: use --network instructor for Hardhat console ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
else
    echo -e "${RED}❌ Unknown mode: $MODE${NC}"
    echo "   Valid modes: instructor, student"
    exit 1
fi

# Keep container running and wait for child processes
wait
