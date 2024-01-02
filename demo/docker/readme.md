see https://raw.githubusercontent.com/moby/moby/master/contrib/download-frozen-image-v2.sh


imageTag="$1"
shift
image="${imageTag%%[:@]*}"
imageTag="${imageTag#*:}"
digest="${imageTag##*@}"
tag="${imageTag%%@*}"


registryBase='https://registry-1.docker.io'
authBase='https://auth.docker.io'
authService='registry.docker.io'

image=library/alpine:3.14
token="$(curl -fsSL "$authBase/token?service=$authService&scope=repository:$image:pull" | jq --raw-output '.token')"

image=library/alpine
digest=
curl -fsSL -H "Authorization: Bearer $token" \
    -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
    -H 'Accept: application/vnd.docker.distribution.manifest.list.v2+json' \
    -H 'Accept: application/vnd.docker.distribution.manifest.v1+json' \
     "$registryBase/v2/$image/manifests/$digest"