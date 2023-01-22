#!/usr/bin/env python
##############################################################################
#
# pydistort         by Frandsen Group
#                     Benjamin A. Frandsen benfrandsen@byu.edu
#                     (c) 2023 Benjamin Allen Frandsen
#                      All rights reserved
#
# File coded by:    Parker Hamilton
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################


"""Tools to interface with ISODISTORT"""

import requests


ISO_UPLOAD_SITE = "https://iso.byu.edu/iso/isodistortuploadfile.php"
ISO_FORM_SITE = "https://iso.byu.edu/iso/isodistortform.php"

def _uploadCIF(cifname):
    """Upload CIF file to ISODISTORT.
    """
    ciffile = open(cifname,'rb')
    up = {'toProcess':(cifname,ciffile),}
    out = requests.post(ISO_UPLOAD_SITE,files=up).text
    ciffile.close

    start = out.index("VALUE=")
    start = out.index('"',start+1)+1
    end = out.index('"',start)
    filename = out[start:end]

    return filename

def _postParentCIF(fname,var_dict):
    """Run "Method 3" on the parent structure.
    """
    up = {'filename':fname,'input':'uploadparentcif'}
    out = requests.post(ISO_FORM_SITE,up)

    data = {}
    line_iter = out.iter_lines()
    for line in line_iter:
        if b"Method 3" in line:
            break

    for line in line_iter:
        if b'INPUT TYPE="hidden"' in line:
            items = line.decode('utf-8').split(' ',3)
            name = items[2].split('=')[1].strip('"')

            val = items[3].split('=',1)[1].strip('>"')
            data[name] = val
        if b'Method 4' in line:
            break

    data['subgroupsym'] = '1 P1 C1-1'
    data['pointgroupsym'] = '0'
    data['latticetype'] = 'direct'
    data['centering'] = 'd'
    data['basis11'] = '1'
    data['basis12'] = '0'
    data['basis13'] = '0'
    data['basis21'] = '0'
    data['basis22'] = '1'
    data['basis23'] = '0'
    data['basis31'] = '0'
    data['basis32'] = '0'
    data['basis33'] = '1'
    for key,value in var_dict.items():
        data[key] = value

    return data

def _postIsoSubGroup(data):
    """Select the distortion mode.
    
    Note: this is only guaranteed to be functional for P1 subgroup symmetry.
    """
    out = requests.post(ISO_FORM_SITE,data=data)
    data = {}
    line_iter = out.iter_lines()

    for line in line_iter:
        if b"<FORM ACTION" in line:
            break

    for line in line_iter:
        if b'INPUT TYPE="hidden"' in line:
            items = line.decode('utf-8').split(' ',3)
            name = items[2].split('=')[1].strip('"')

            val = items[3].split('=',1)[1].strip('>"')
            data[name] = val

        if b'RADIO' in line and b'CHECKED' in line:
            items = line.decode('utf-8').split(' ',3)
            name = items[2].split('=')[1].strip('"')

            val = items[3].split('=',1)[1].strip('>"')
            data[name] = val

        if b'</FORM>' in line:
            break

    return data

def _postDistort(data, format):
    """Prepare the data for downloading.
    """
    out = requests.post(ISO_FORM_SITE,data=data)

    data = {}
    line_iter = out.iter_lines()
    for line in line_iter:
        if b"<FORM ACTION" in line:
            break

    for line in line_iter:
        if b'INPUT TYPE="hidden"' in line:
            items = line.decode('utf-8').split(' ',3)
            name = items[2].split('=')[1].strip('"')

            val = items[3].split('=',1)[1].strip('>"')
            data[name] = val

        if b'input type="text"' in line:
            items = line.decode('utf-8').split(' ',5)
            name = [s for s in items if 'name=' in s][0].split('=')[1].strip('"')

            val = [s for s in items if 'value=' in s][0].split('=')[1].strip('"')
            data[name] = val

        if b'RADIO' in line and b'CHECKED' in line:
            items = line.decode('utf-8').split(' ',3)
            name = items[2].split('"')[1]

            val = items[3].split('"')[1]
            data[name] = val

        if b'</FORM>' in line:
            break

    data['origintype'] = format
    return data

def _postDisplayDistort(data,fname):
    """Download the ISODISTORT output.
    """
    out = requests.post(ISO_FORM_SITE,data=data)
    open(fname,'wb').write(out.text.encode('utf-8'))

def get(cifname,outfname,var_dict={},format='topas'):
    """
    Interacts with the Isodistort website to get the available distortion modes. It is set to use Method 3 
    and assumes P1 symmetry by default.

    params:
        cifname: str
            The name of the local cif file you want to use
        outfname: str
            The name of the file where you want the distortion modes saved, should be a ,str file
        var_dict: dict
            Variables to pass to Method 3 in ISODISTORT to setup the symmetry, lattice, and basis.
            Defaults to P1 symmetry and a identity matrix for the basis.
            Keys and default values are:
                'subgroupsym' = '1 P1 C1-1'
                'pointgroupsym' = '0'
                'latticetype' = 'direct'
                'centering' = 'd' (for default)
                'basis11' = '1'
                'basis12' = '0'
                'basis13' = '0'
                'basis21' = '0'
                'basis22' = '1'
                'basis23' = '0'
                'basis31' = '0'
                'basis32' = '0'
                'basis33' = '1'
            Note that the 'subgroupsym' value can simply be the space group
            number (as a string) for the desired subgroup. It is not
            recommended to use the space group symbol alone, since this is
            not always read correctly.
        format: str
            Format of the output file requested from the ISODISTORT server.
            Allowed values are:
                'isovizdistortion'
                'isovizdiffraction'
                'structurefile'
                'distortionfile'
                'domains'
                'primary'
                'modesdetails'
                'completemodesdetails'
                'topas'
                'fullprof'
                'irreps'
                'tree'
            See https://stokes.byu.edu/iso/isodistorthelp.php#savedist for
            information about each format. 
    """
    ### check that the format is acceptable
    formatlist = ['isovizdistortion',
                  'isovizdiffraction',
                  'structurefile',
                  'distortionfile',
                  'domains',
                  'primary',
                  'modesdetails',
                  'completemodesdetails',
                  'topas',
                  'fullprof',
                  'irreps',
                  'tree']
    
    if format not in formatlist:
        print('This is not a valid format. Acceptable options are:\n')
        print('isovizdistortion')
        print('isovizdiffraction')
        print('structurefile')
        print('distortionfile')
        print('domains')
        print('primary')
        print('modesdetails')
        print('completemodesdetails')
        print('topas')
        print('fullprof')
        print('irreps')
        print('tree\n')
        print('Please try again with one of these formats.')
    else:    
        parentcif = _uploadCIF(cifname)
        data = _postParentCIF(parentcif,var_dict)
        data = _postIsoSubGroup(data)
        data = _postDistort(data, format)
        _postDisplayDistort(data,outfname)