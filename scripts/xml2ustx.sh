#!/bin/zsh

DIR=$(cd "$(dirname $0)/.." && pwd)
RUN="$DIR/run.sh"
"$RUN" "$@"
