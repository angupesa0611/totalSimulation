#!/bin/bash
# =============================================================================
# Sequential Docker Compose Build Script
# Builds containers one at a time to prevent OOM on 15GB RAM server.
#
# Usage:
#   ./scripts/build.sh              # Build all (only changed containers rebuild)
#   ./scripts/build.sh client       # Build specific service(s)
#   ./scripts/build.sh --no-cache   # Force rebuild without cache
#   ./scripts/build.sh --pull       # Pull latest base images before building
# =============================================================================

set -euo pipefail
cd "$(dirname "$0")/.."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
BUILD_ARGS=()
SERVICES=()
for arg in "$@"; do
    case "$arg" in
        --no-cache|--pull|--quiet|-q)
            BUILD_ARGS+=("$arg")
            ;;
        *)
            SERVICES+=("$arg")
            ;;
    esac
done

# Build order: heaviest base images first (so pulls finish while lighter ones build),
# then containers that compile from source, then the rest.
# This order minimizes peak memory usage.
ALL_SERVICES=(
    # Pre-built heavy base images (just pull + pip install, but large downloads)
    einstein-toolkit-worker
    firedrake-worker
    nest-worker
    fenics-worker
    sagemath-worker
    openfoam-worker

    # Conda-based (moderate memory: conda solve + install)
    openmm-worker
    psi4-worker
    dedalus-worker
    meep-worker
    qmmm-worker
    gromacs-worker
    su2-worker
    slim-worker

    # Source compilation (high memory: LAMMPS build)
    orchestrator

    # Lighter builds
    qe-worker
    elmer-worker
    namd-worker
    vtk-worker
    manim-worker

    # Lightest (multi-stage, small final image)
    client
)

# Use specific services if provided, otherwise build all
if [ ${#SERVICES[@]} -gt 0 ]; then
    BUILD_LIST=("${SERVICES[@]}")
else
    BUILD_LIST=("${ALL_SERVICES[@]}")
fi

echo -e "${CYAN}=== Sequential Build ===${NC}"
echo -e "Services to build: ${#BUILD_LIST[@]}"
echo -e "Build args: ${BUILD_ARGS[*]:-none}"
echo ""

FAILED=()
SKIPPED=()
BUILT=()
START_TIME=$SECONDS

for service in "${BUILD_LIST[@]}"; do
    echo -e "${YELLOW}[$((${#BUILT[@]} + ${#FAILED[@]} + ${#SKIPPED[@]} + 1))/${#BUILD_LIST[@]}] Building ${service}...${NC}"
    SVC_START=$SECONDS

    if docker compose build "${BUILD_ARGS[@]}" "$service" 2>&1 | tail -3; then
        elapsed=$(( SECONDS - SVC_START ))
        echo -e "${GREEN}  ✓ ${service} built (${elapsed}s)${NC}"
        BUILT+=("$service")
    else
        elapsed=$(( SECONDS - SVC_START ))
        echo -e "${RED}  ✗ ${service} FAILED (${elapsed}s)${NC}"
        FAILED+=("$service")
    fi
    echo ""
done

# Summary
TOTAL_TIME=$(( SECONDS - START_TIME ))
echo -e "${CYAN}=== Build Summary ===${NC}"
echo -e "Total time: $((TOTAL_TIME / 60))m $((TOTAL_TIME % 60))s"
echo -e "${GREEN}Built: ${#BUILT[@]}${NC}"
[ ${#FAILED[@]} -gt 0 ] && echo -e "${RED}Failed: ${FAILED[*]}${NC}"
echo ""

if [ ${#FAILED[@]} -gt 0 ]; then
    echo -e "${RED}Some builds failed. Fix errors and re-run:${NC}"
    echo -e "  ./scripts/build.sh ${FAILED[*]}"
    exit 1
fi

# Pre-create worker containers (stopped) from already-built images.
# Uses --no-build so it skips any worker whose image hasn't been built yet.
echo -e "${CYAN}Creating worker containers (stopped, for on-demand startup)...${NC}"
if docker compose --profile workers create --no-build 2>&1 | tail -5; then
    echo -e "${GREEN}  ✓ Worker containers created${NC}"
else
    echo -e "${YELLOW}  ⚠ Some worker containers could not be created (images not built yet).${NC}"
    echo -e "${YELLOW}    Build missing workers with: ./scripts/build.sh <worker-name>${NC}"
fi
echo ""

echo -e "${GREEN}All builds succeeded. Start with:${NC}"
echo -e "  docker compose up -d"
echo -e ""
echo -e "${CYAN}Note: Workers start on-demand when simulations are submitted.${NC}"
echo -e "  To start all workers manually: docker compose --profile workers up -d"
