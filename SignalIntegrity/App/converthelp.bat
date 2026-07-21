::  DEPRECATED - the LyX + eLyXer help workflow has been retired.
::
::  The help system is now built with MkDocs. See:
::      SignalIntegrityPages/SignalIntegrity/App/Help/README.md
::
::  To build the help site:
::      cd <pages>/SignalIntegrity/App/Help
::      build.bat        (runs mkdocs build + gen_helpkeys.py)
::
::  To regenerate Markdown from Help.lyx (needs lyx + pandoc):
::      python convert_help.py
::
echo This converter is deprecated. See Help/README.md for the MkDocs workflow.
