#!/bin/bash

memcache_installed=`dpkg -l | grep -i 'memcached' | wc -l`
if [ "$memcache_installed" == "0" ]; then
    echo "Installing memcached"
    apt-get install memcached
fi

perl_memcache_installed=`perl -e 'use Cache::Memcached::Fast'`
if [ "$perl_memcache_installed" == "1" ]; then
    echo "Installing perl Cache::Memcached::Fast"
    perl -MCPAN -e 'install Cache::Memcached::Fast'
fi

python_memcache_installed=`pip list | grep -i 'pymemcache' | wc -l`
if [ "$python_memcache_installed" == "0" ]; then
    echo "Installing python pymemcache"
    pip install pymemcache
fi

