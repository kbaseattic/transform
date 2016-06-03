#!/usr/bin/env bash

GIT=git
GITHUB_URL='https://github.com'

mkdir clonetemp

for dep in  'kbase/user_and_job_state' 'kbase/workspace_deluxe' \
           'mlhenderson/handle_service' 'kbase/kbapi_common'
do
    url="$GITHUB_URL/$dep"
    cmd="$GIT clone $url"
    printf "RUN: %s\n" "$cmd"
    cd clonetemp
    $cmd
    depdir=`basename $dep`
    libdir="$depdir/lib/biokbase"
    rm -f $libdir/__init__.py
    printf "Copying $libdir/* into biokbase\n"
    cp -r $libdir/* ../biokbase/
    cd ..
done

# library needed for filemagic
brew install libmagic