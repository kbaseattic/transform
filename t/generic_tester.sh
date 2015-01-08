#!/usr/bin/env bash

if [ -z "$KB_TOP" ]; then
	echo "Need to set KB ENV variables";
	echo "Error: Please source /kb/deployment/user-env.sh if it is standard KBase VM";
	exit 1;
fi

DENV=$(echo "$KB_TOP" | grep "deployment" | wc -l);

if (( $DENV != 1 )); then
	echo "Warning: Need to source deployment  environment";
	#exit 2;
fi

if (( $# != 6 )); then
	echo "Usage: $0 <config_fn> <func> <mode> <ext_type> <kb_type> <sub_filter>";
	echo "  i.g. : transform/t/generic_tester.sh transform/deploy.cfg.test validate hndlr '*' '*' '*'";
	exit 3;
fi

CFG=`readlink -f $1`;
FUNC=$2
MODE=$3
EXT=$4;
KB=$5;
SUB=$6;

FFUNC=$FUNC;
if [ "$FUNC" == "validate" ]; then
  FFUNC="upload";
fi

WDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd );
cd $WDIR;

ES=0;
for i in `ls configs/$FFUNC-*$EXT*-*$KB*-*$SUB*.json`; do
 echo "perl generic_tester.t $CFG $i $FUNC $MODE";
 echo "$(perl generic_tester.t $CFG $i $FUNC $MODE)";
 if (( $? != 0 )); then
   ES=$?;
 fi
done
exit $ES
