pip install requests_toolbelt filemagic ftputil
python_metatlas_installed=`pip list | grep '^metatlas (' | wc -l`
if [ "$python_metatlas_installed" == "0" ]; then
    pip install git+https://github.com/metabolite-atlas/metatlas
fi
