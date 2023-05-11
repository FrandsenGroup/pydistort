#!/usr/bin/env python
##############################################################################
#
# pydistort         by Frandsen Group
#                     Benjamin A. Frandsen benfrandsen@byu.edu
#                     (c) 2023 Benjamin Allen Frandsen
#                      All rights reserved
#
# File coded by:    Tobias Bird
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
# We acknowledge Brian Toby and Robert Von Dreele as the first to develop a
# python interface to ISODISTORT, which served as a valuable starting point
# for this package. Their work can be found as part of the GSAS-II software at
# https://subversion.xray.aps.anl.gov/trac/pyGSAS/browser/trunk/ISODISTORT.py
##############################################################################
"""Tools to interface with ISODISTORT and the ISOTROPY software suite"""

import requests

ISO_UPLOAD_SITE = "https://iso.byu.edu/iso/findsymuploadfile.php"
ISO_FORM_SITE = "https://iso.byu.edu/iso/findsymform.php"

def _uploadCIF(cif):
    """Upload CIF to FINDSYM.
    """
    f = open(cif,'rb')
    up = {'toProcess':(cif,f),}
    out = requests.post(ISO_UPLOAD_SITE,files=up).text
    f.close()

    start = out.index("VALUE=")
    start = out.index('"',start+1)+1
    end = out.index('"',start)
    fname = out[start:end]

    return fname

def _postsymCIF(fname, outfname):
    """Return symmetrised CIF from FINDSYM
    """
    up = {'filename': fname, 'input': 'uploadparentcif'}
    out = requests.post(ISO_FORM_SITE, up)

    line_iter = out.iter_lines()
    start = False
    flines = []

    for line in line_iter:
        if b"data_findsym-output" in line:
            start = True
        if start:

            flines.append(line.decode('utf-8'))
        if b"# end of cif" in line:
            start = False

    f = open(outfname, "w")
    for entry in flines:
        entry += "\n"
        f.write(entry)
    f.close()



def get_sym(cif, outfname):
    """Create symmetrised CIF from uploaded CIF
    """
    fname = _uploadCIF(cif)
    _postsymCIF(fname, outfname)
