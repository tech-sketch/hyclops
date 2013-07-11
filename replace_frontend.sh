#!/bin/sh

target_frontend_dir=$1
zabbix_version=$2
if [[ ! $zabbix_version =~ ^(2.0|2.2)$ ]]; 
then
    echo "Not supported version (Supported only 2.0 or 2.2)"
    exit 1
fi

source_dir=`dirname ${0}`"/misc/zabbix-custom/$zabbix_version"

if [ -d $target_frontend_dir ]; 
then
    echo "Replace and copy some files..."
    if [ -f $target_frontend_dir/dashboard.php.orig ];
    then
        cp -r -a $source_dir/* $target_frontend_dir
        exit 0
    fi
    cp -r -a --backup=nil -S ".orig" $source_dir/* $target_frontend_dir
    exit 0
fi
echo "No such directory $target_frontend_dir"
exit 1 
