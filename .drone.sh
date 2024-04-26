#!/bin/bash

if [ -z "${DRONE_COMMIT_SHA:0:7}" ]
then export TAG=${IMAGETAG}
else export TAG=${DRONE_COMMIT_SHA:0:7}
fi

mkdir -p $HOME/.ssh
echo "$SSH_KEY" > $HOME/.ssh/ed25519
chmod 600 $HOME/.ssh/ed25519
ssh-keyscan bitbucket.org > /$HOME/.ssh/known_hosts
cat <<EOT >> $HOME/.ssh/config
    Host bitbucket.org
    HostName bitbucket.org
    User git
    IdentityFile ~/.ssh/ed25519
EOT

echo "${PROJECT:0:3}-helm-charts repository cloning"

if git clone git@bitbucket.org:creativeadvtech/${PROJECT:0:3}-helm-charts.git helm-charts; then
    cd helm-charts
else
    exit 1
fi

git checkout master && git branch --set-upstream-to=origin master


yq e -i '(.image.tag) = strenv(TAG)' cms/values-${ENV}.yaml
yq e -i '(.image.tag) = strenv(TAG)' lms/values-${ENV}.yaml
helm secrets lint -f cms/values-staging.yaml -f cms/secrets-${ENV}.enc.yaml cms/
helm secrets lint -f lms/values-staging.yaml -f lms/secrets-${ENV}.enc.yaml lms/

if git add --all && git commit -m "lms and cms service's image tags updated to $TAG" && git push -u origin master; then
    echo "**SUCCESS** CMS and LMS service's will be deployed soon"
    argocd login --username $ARGOCD_USERNAME --password $ARGOCD_PASSWORD argocd.creativeadvtech.ml
    argocd app get --grpc-web ${PROJECT}-${ENV}-cms --hard-refresh
    argocd app get --grpc-web ${PROJECT}-${ENV}-lms --hard-refresh
    argocd app wait --grpc-web ${PROJECT}-${ENV}-cms
    argocd app wait --grpc-web ${PROJECT}-${ENV}-lms
else
    echo "**WARNING** nothing has changed, exit"
fi
