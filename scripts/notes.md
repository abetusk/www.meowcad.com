Component and Modules Library File Uploads
============

This is a quick summary of the import modules and components
functionality of MeowCAD.

As of this writing, only portfolio wide uploads are working, but
the hope is to extend it be used in projects as well.

User Workflow
-------------

The basic workflow from the user side is to go to an 'import'
tab on the portfolio/project page, select files to upload, either
from a local file or from a git repository, and then, after
a refresh/reload/magic have the component/module lists be available
to the portfolio/project and to the schematic/board editor.

Backend Design
--------------

There are three major portions in a library upload:

  - Receive the file
  - Uncompress the file, find the .lib/.mod and convert
  - Create the snapshots for the converted library

Since each step is potentially time consuming, they have been split.
Though independent programs/daemons, they communicate through a series
of entries in the backend Redis database or files sprinkled throughout the
system (described below).

### File Receipt

`libmodImport.py`

The file is received and put into a staging area.  In addition,
a call to `meowaux.queueImport` is called that adds a `(queue_id)`
to the Redis `importq` list and a hash entry `importq:(queue_id)`
with information on when it was uploaded, which user it belongs to
and where the file can be located.

### Decompression and Conversion

`libmod_import_d.py`, `libmod_import_file.py`, `libmodloclist.py`

`libmod_import_d.py` is constantly running and monitoring the `importq`.
Once it finds a `(queue_id)`, it removes it from the `importq` and retrieves
the `importq:(queue_id)` entry.

For each entry, `libmod_import_file.py` is called to decompress and copy
over the converted files into the users base directory (for portfolios) or
project directory (for project specific libraries).

`libmod_import_file.py` creates location and list files for each of the component
library or module library processed.  `libmod_import_file.py` put these into a
`json` subdirectory in the base directory.  Each of these files is preceded with
a unique id.  For example:

    json/ffd43202-cd96-4536-9a9d-52496601aae8_component_list.json
    json/ffd43202-cd96-4536-9a9d-52496601aae8_component_location.json
    json/ffd43201-cd96-4536-9a9d-52496601aae8_footprint_list.json
    json/ffd43202-cd96-4536-9a9d-52496601aae8_footprint_location.json

There should only every be 0, 2 or 4 files written, depending on whether there was
no input or an err, only one of the componet library or module library types processed,
or whether both component and module libraries were processed.

Each of the list and location files that is generated are print out to stdout after creation.

`libmod_import_d.py` then calls the `libmodloclist.py` to consolodate the json files into
the final location and list files.  The input files are put into the `json/.store` direcotory
after processing.  The final files from `libmodloclist.py` should be a potentially inclusive
sub-set of the following files:


    json/component_list.json
    json/component_location.json
    json/footprint_list.json
    json/footprint_location.json

Finally, `libmod_import_d.py` creates a 'queue file' and puts it into the 'snap queue directory'
(currently `/home/meow/queue`).  The queue file is a comma seperated file, with the fileId of
the current file in the queue directory, the fully qualified file name of the new json library 
directory location, the user id, and the project id (if applicable).

### Snapshot Creation

`libmod_snap_d.py`, `libsnap.js`, `modsnap.js`

The `libmod_snap_d.py` process monitors the queue directory for any new files.  It then
goes through and calls `libsnap.js` or `modsnap.js` appropriately to create the snapshot
for the component or module library element

After a queue file is processed, it is put into the queue directories `.store` sub directory.


Miscellaneous
-------------

For the location and list json files, the locations are double URL escaped, with the additional
escaping of the forward slash (`/`).  This facilites ease of use in the JavaScript application.

