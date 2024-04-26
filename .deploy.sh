#!/bin/bash
set -e

export TAG=${IMAGETAG}

yq e -i '(.image.tag) = strenv(TAG)' cms/values-${ENV}.yaml
yq e -i '(.image.tag) = strenv(TAG)' lms/values-${ENV}.yaml
helm secrets lint -f cms/values-staging.yaml -f cms/secrets-${ENV}.enc.yaml cms/
helm secrets lint -f lms/values-staging.yaml -f lms/secrets-${ENV}.enc.yaml lms/

checkout() {
    git add --all && \
    git commit -m "lms and cms service's image tags updated to $TAG" &&  \
    git push -u origin HEAD:master
}

if (checkout; [ $? -eq 0 ]) ; then
    echo "**SUCCESS** CMS and LMS services will be deployed soon"
    argocd login --username $ARGOCD_USERNAME --password $ARGOCD_PASSWORD argocd.creativeadvtech.ml
    argocd app get --grpc-web ${PROJECT}-${ENV}-cms --hard-refresh
    argocd app get --grpc-web ${PROJECT}-${ENV}-lms --hard-refresh
else
    echo "**WARNING** nothing has changed, exit"
fi
