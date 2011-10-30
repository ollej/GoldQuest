#!/bin/sh
BASE_DIR=`dirname "$0"`

FRAMEWORK_LN=$BASE_DIR/appengine-web/src/GoldFrame

if [ -e $FRAMEWORK_LN ]
then
    echo "$FRAMEWORK_LN exists. aborting."
    exit 1
fi

echo "creating symlink $FRAMEWORK_LN"
ln -s ../../src $FRAMEWORK_LN
