KBase Transform v0.1
================

<i><compact>More than meets the eye?</compact></i>

The KBase Transform service has responsibilities for 3 data tasks:

<ul>
<li>
<b>Upload</b> - Transforming data from external community formats to KBase typed data
</li>
<li>
<b>Download</b> - Transforming KBase typed data into external community formats
</li>
<li>
<b>Convert</b> - Transforming one KBase type to another KBase type
</li>
</ul>

Scripts responsible for data validation, transformations, conversions are located in the plugins folder as well as a configuration file for each script.

## Development

See plugins/examples and plugins/templates for making your own script for upload/download/convert.

Use a test driver script to demo the available functionality and data transformations.

<pre>
git clone https://kbase.us/kbase/transform

cd transform/t/demo

# build a local virtualenv
python setup.py

# see some example data uploads
venv/bin/python bin/upload.py --demo

# read the docs for using your own data
venv/bin/python bin/upload.py --help
</pre>
