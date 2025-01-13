#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------
# Color Definitions
# --------------------------------------------

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --------------------------------------------
# Function Definitions
# --------------------------------------------

# Function to log messages with timestamp and color
log() {
    local level="$1"
    shift
    local message="$*"

    case "$level" in
        INFO)
            echo -e "${GREEN}[INFO] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
        SUCCESS)
            echo -e "${BLUE}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
        DEBUG)
            echo -e "${CYAN}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
        *)
            echo -e "${NC}[UNKNOWN] $(date '+%Y-%m-%d %H:%M:%S'):${NC} $message"
            ;;
    esac
}

# Function to check if a specific port is in use
is_port_in_use() {
    local port=$1
    if lsof -i :"$port" >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to list all .json files in characters/ directory and join them with commas
get_characters_argument() {
    local dir="characters"
    local files=("$dir"/*.json)

    # Check if there are any .json files
    if [ ! -e "${files[0]}" ]; then
        log "ERROR" "No .json files found in $dir directory."
        exit 1
    fi

    # Join filenames with commas
    local characters=""
    for file in "${files[@]}"; do
        if [ -z "$characters" ]; then
            characters="$file"
        else
            characters="$characters,$file"
        fi
    done

    echo "characters=$characters"
}

# Function to start a background process using pnpm with arguments
start_pnpm_process() {
    local script=$1
    shift
    local args=("$@")
    local log_file=$2
    local port=$3

    if is_port_in_use "$port"; then
        log "WARN" "Port $port is already in use. Skipping start of process '$script'."
    else
        if [ -z "${args[*]}" ]; then
            log "INFO" "Starting process '$script' on port $port without additional arguments."
        else
            log "INFO" "Starting process '$script' on port $port with arguments: ${args[*]}"
        fi

        # Use 'pnpm run' to execute scripts defined in package.json
        # '--' separates pnpm arguments from script arguments
        nohup pnpm run "$script" -- "${args[@]}" > "$log_file" 2>&1 &
        local pid=$!
        echo "$pid" > "${log_file%.log}.pid"
        log "DEBUG" "Process '$script' started with PID $pid. Logs: $log_file"

        log "DEBUG" "Sleep 10s"
        sleep 10  # Allow some time for the process to start

        if is_port_in_use "$port"; then
            log "SUCCESS" "Process '$script' is running successfully on port $port."
        else
            log "ERROR" "Failed to start process '$script' on port $port. Check $log_file for details."
            exit 1
        fi
    fi
}

# Function to handle shutdown signals
shutdown() {
    log "INFO" "◎ Received shutdown signal, closing server and client..."

    # Stop server
    if [ -f "server.pid" ]; then
        local server_pid
        server_pid=$(cat "server.pid")
        if kill "$server_pid" >/dev/null 2>&1; then
            log "INFO" "Sent SIGTERM to server (PID $server_pid)."
        else
            log "WARN" "Failed to send SIGTERM to server (PID $server_pid)."
        fi
    fi

    # Stop client
    if [ -f "client.pid" ]; then
        local client_pid
        client_pid=$(cat "client.pid")
        if kill "$client_pid" >/dev/null 2>&1; then
            log "INFO" "Sent SIGTERM to client (PID $client_pid)."
        else
            log "WARN" "Failed to send SIGTERM to client (PID $client_pid)."
        fi
    fi

    # Wait for processes to terminate
    sleep 3

    # Verify if processes are terminated
    if [ -f "server.pid" ] && kill -0 "$(cat "server.pid")" >/dev/null 2>&1; then
        log "WARN" "Server (PID $(cat server.pid)) did not terminate. Sending SIGKILL..."
        kill -9 "$(cat server.pid)" || true
    fi

    if [ -f "client.pid" ] && kill -0 "$(cat "client.pid")" >/dev/null 2>&1; then
        log "WARN" "Client (PID $(cat client.pid)) did not terminate. Sending SIGKILL..."
        kill -9 "$(cat client.pid)" || true
    fi

    log "SUCCESS" "✓ Server and client closed successfully."
    exit 0
}

# Function to check if required commands are available
check_dependencies() {
    for cmd in pnpm lsof; do
        if ! command -v "$cmd" &> /dev/null; then
            log "ERROR" "Required command '$cmd' is not installed."
            exit 1
        fi
    done
}

# --------------------------------------------
# Script Execution
# --------------------------------------------

# Set trap for SIGINT and SIGTERM to handle graceful shutdown
trap shutdown SIGINT SIGTERM

# Check for required dependencies
check_dependencies

# Verify that ELIZA_PATH environment variable is set
if [ -z "${ELIZA_PATH:-}" ]; then
    log "ERROR" "ELIZA_PATH environment variable is not set."
    exit 1
fi

# Navigate to the ELIZA_PATH directory
cd "$ELIZA_PATH"
log "INFO" "Navigated to ELIZA_PATH: $ELIZA_PATH"

# Get characters argument
characters_arg=$(get_characters_argument)

# Extract characters value
characters_value="${characters_arg#characters=}"
log "INFO" "Loaded characters: ${characters_value//,/ , }"

# Start Eliza Server on port 3000
# Ensure that your package.json has a script named "start" that accepts the --characters argument
start_pnpm_process "start" "--characters=$characters_value" "server.log" 3000

# Start Eliza Client on port 5173
# Ensure that your package.json has a script named "start:client"
start_pnpm_process "start:client" "" "client.log" 5173

# Final Log Messages
log "INFO" "=================================================="
log "INFO" "Eliza server and client processes started in background."
log "INFO" " - Server logs:  $ELIZA_PATH/server.log"
log "INFO" " - Client logs:  $ELIZA_PATH/client.log"
log "INFO" " - Loaded Agents: ${characters_value//,/ , }"
log "INFO" "Check with check_server.sh and check_client.sh scripts."
log "INFO" "=================================================="

# Keep the script running to handle signals
# This can be done using 'wait' if you want to wait for background processes,
# but since we have PID files, we'll use an infinite loop
while true; do
    sleep 1
done
