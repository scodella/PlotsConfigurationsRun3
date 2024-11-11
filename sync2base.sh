#!/bin/sh -x
git checkout base
git fetch
#git pull
git checkout RPLME_ANALYSIS
git merge origin/base

