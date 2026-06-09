#!/usr/bin/env bash
set -euo pipefail

APP_NAME="module-talkingdb"
IMAGE="$APP_NAME"

GCP_PROJECT="${GCP_PROJECT:-talkingdb-40099}"
ARTIFACT_REPO="${ARTIFACT_REPO:-tdb}"
ARTIFACT_REGION="${ARTIFACT_REGION:-us-central1}"

REGISTRY_HOST="${ARTIFACT_REGION}-docker.pkg.dev"
REMOTE_IMAGE="$REGISTRY_HOST/$GCP_PROJECT/$ARTIFACT_REPO/$IMAGE"

USE_GIT_TAG="${USE_GIT_TAG:-true}"
CUSTOM_TAG="${CUSTOM_TAG:-}"

die(){ echo "ERROR: $*" >&2; exit 1; }
log(){ printf "\n[%s] %s\n" "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"; }

CURRENT_COMMIT="$(git rev-parse --short HEAD)"

log "Building Docker image: $IMAGE:latest"
export DOCKER_BUILDKIT=1

docker build \
  -t "$IMAGE:latest" \
  .

TAGS_TO_PUSH=("latest")

if [[ "$USE_GIT_TAG" == "true" ]]; then
  docker tag "$IMAGE:latest" "$IMAGE:$CURRENT_COMMIT"
  TAGS_TO_PUSH+=("$CURRENT_COMMIT")
fi

if [[ -n "$CUSTOM_TAG" ]]; then
  docker tag "$IMAGE:latest" "$IMAGE:$CUSTOM_TAG"
  TAGS_TO_PUSH+=("$CUSTOM_TAG")
fi

log "Configuring Docker auth for Artifact Registry"
gcloud auth configure-docker \
  "$REGISTRY_HOST" \
  --quiet

log "Tagging + pushing to Artifact Registry: $REMOTE_IMAGE"
for tag in "${TAGS_TO_PUSH[@]}"; do
  docker tag "$IMAGE:$tag" "$REMOTE_IMAGE:$tag"
  log "Pushing $REMOTE_IMAGE:$tag"
  docker push "$REMOTE_IMAGE:$tag"
done

log "Build completed and pushed tags:"
printf "  %s\n" "${TAGS_TO_PUSH[@]}"

docker images | grep -E "^REPOSITORY|$IMAGE|$REMOTE_IMAGE"
