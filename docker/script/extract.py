#!/usr/bin/env python3

###
## do the relevant imports
###

import errno
import json
import os
import sys
import time

from base64             import b64decode
from datetime           import datetime, timedelta
from distutils.util     import strtobool
from dotenv             import load_dotenv
from pathlib            import Path
from watchdog.events    import FileSystemEventHandler
from watchdog.observers import Observer

###
## Helper function – Python CLI history
##    Very useful during development
###

def history ( lineNumbers=True ):
  import readline
  if lineNumbers:
    formatstring = '{0:4d}  {1!s}'
  else:
    formatstring = '{1!s}'
  for i in range( 1, readline.get_current_history_length() + 1 ):
    print( formatstring.format( i, readline.get_history_item( i ) ) )

###
## define global functions
###

# Date-String
def current_dt ( dt_format='%Y-%m-%d %H:%M.%S' ):
    now = datetime.now()
    return now.strftime( dt_format )

# Error print when in debug mode
def e_print ( msg, colorcode=None ):
    if colorcode == None:
        colorcode = COLOR.error
    global debug
    if debug:
        sys.stderr.write( colorcode + current_dt() + ': ' + msg + COLOR.reset + "\n" )

# Regular print when in debug mode
def r_print ( msg, colorcode=None ):
    if colorcode == None:
        colorcode = COLOR.info
    global debug
    if debug:
        sys.stderr.write( colorcode + current_dt() + ': ' + msg + COLOR.reset + "\n" )

# convert string to boolean
def bool_val ( str_val ):
    return bool( strtobool( str_val ) )

# ensure keys to be lowercase
def dict_keys_to_lower ( cur_object ):
    if isinstance( cur_object, dict ):
        result = {}
        for key, value in cur_object.items():
            if isinstance( value, dict ) or isinstance( value, list ):
                value = dict_keys_to_lower( value )
            result[ key.lower() ] = value
    elif isinstance(cur_object, list):
        result = []
        for value in cur_object:
            if isinstance( value, dict ) or isinstance( value, list ):
                value = dict_keys_to_lower( value )
            result.append( value )
    else:
        e_print( 'something with your object to ensure lowercase keys went wront ...' )
        sys.exit(4)
    return result

def prepare_url ( url ):
    return url.lower().replace( '*', asterisk )

###
## fetch variables from ENV
###

load_dotenv()

acme_file = os.getenv( "ACMEFILE",         "acme.json" )
acme_dir  = os.getenv( "ACMEDIR",          "/acme" )
asterisk  = os.getenv( "REPLACE_ASTERISK", "STAR" )
certs_dir = os.getenv( "CERTSDIR",         "/certs" )
work_dir  = os.getenv( "WORKDIR",          "/certs_extract" )
crt_split = os.getenv( "CERTSPLIT",        "-----BEGIN CERTIFICATE-----" )

limitfqdn = list( filter( None, [ s.strip() for s in os.getenv( "LIMIT_FQDN", ""  ).split( ',' ) ] ))

debug     = bool_val( os.getenv( "DEBUG", "False" ) )
flat_crts = bool_val( os.getenv( "STORE_FLAT_CRTS", "True" ) )
archive   = bool_val( os.getenv( "CRT_ARCHIVE", "True" ) )

acme_path = os.path.join( acme_dir, acme_file )

class COLOR():
    error   = '\u001b[' + os.getenv( 'COLOR_ERROR',   "1;31" ) + 'm'
    info    = '\u001b[' + os.getenv( 'COLOR_INFO',    "0" ) + 'm'
    success = '\u001b[' + os.getenv( 'COLOR_SUCCESS', "0;32" ) + 'm'
    warn    = '\u001b[' + os.getenv( 'COLOR_WARN',    "0;33" ) + 'm'
    reset   = '\u001b[0m'

###
## define function to handle the ACME file
###

def handle_acme ( acme_path ):
    # Read ACME data from JSON file
    with open( acme_path ) as acme_open:
        acme_data = json.load( acme_open )

    # determine certificates
    acme_certs   = []
    acme_version = 2
    if acme_data.get( 'DomainsCertificate', False ):
        r_print( 'Handling ACME v1' )
        acme_version = 1
        acme_certs += acme_data['DomainsCertificate']['Certs']
    elif acme_data.get( 'Certificates', False ):
        r_print( 'Handling ACME v2' )
        acme_certs += acme_data['Certificates']
    else:
        # from Træfik v2, there can be multiple challenges ...
        for key, challenge in acme_data.items():
            if acme_data[key].get( 'Certificates', False ):
                r_print( 'Handling ACME v2 within challenge "' + key + '"' )
                acme_certs += acme_data[key]['Certificates']
            else:
                e_print( 'There is a challenge within the ACME file that cannot be handled: ' + key )

    r_print( 'The ACME file "' + acme_path + '" contains ' + str( len( acme_certs ) ) + ' certificate(s), challenged by ACME version ' + str( acme_version ), COLOR.warn )

    # for better key handling, we'll convert all dictionary keys to lower case
    acme_certs = dict_keys_to_lower( acme_certs )
    for cert in acme_certs:
        handle_cert( cert, acme_version )

###
## function for certificate extraction
###

def handle_cert ( cert, acme_version ):

    # fetch relevant data
    c = {}
    c['sans'] = []
    if acme_version == 1:
        c['name'] = cert['certificate']['domain']
        c['pkey'] = cert['certificate']['privatekey']
        c['full'] = cert['certificate']['certificate']
        try:
            c['sans'] = cert['domains']['sans']
        except:
            pass
    elif acme_version == 2:
        c['name'] = cert['domain']['main']
        c['pkey'] = cert['key']
        c['full'] = cert['certificate']
        try:
            c['sans'] = cert['domain']['sans']
        except:
            pass
    else:
        e_print( 'You have an unknown ACME version in your ACME file that should not be possible with this script O.o ...' )

    # retrieve relevant information by decoding Base64
    c['pkey']  = b64decode( c['pkey'] ).decode( 'utf-8' )
    c['full']  = b64decode( c['full'] ).decode( 'utf-8' )

    # split full certificate chain to cert and chain
    ci         = c['full'].find( crt_split, 1 )
    c['crt']   = c['full'][0:ci]
    c['chain'] = c['full'][ci:]

    store_cert( c )

###
## function that stores the certificates as files
###

def store_cert ( cert ):

    cdate = current_dt( '%Y%m%d%H%M%S' )

    ## define all contents to be written to files

    # main certificate
    certfiles = {
        os.path.join( 'certs', prepare_url( cert['name'] ) ): {
            'privkey.pem':   'pkey',
            'cert.pem':      'crt',
            'chain.pem':     'chain',
            'fullchain.pem': 'full'
        }
    }

    # look for SANs
    if len( cert['sans'] ) > 0:
        for name in cert['sans']:
            certfiles[ os.path.join( 'certs', prepare_url( name ) ) ] = {
                'privkey.pem':   'pkey',
                'cert.pem':      'crt',
                'chain.pem':     'chain',
                'fullchain.pem': 'full'
            }

    # Which URLs are covered by this certificate?
    certnames = [ cert['name'] ] + cert['sans']

    # define flat certificates
    if flat_crts:
        for cn in certnames:
            cn = prepare_url( cn )
            try:
                certfiles['flat']
            except:
                certfiles['flat'] = {}
            certfiles['flat'][ cn + '.key' ]       = 'pkey'
            certfiles['flat'][ cn + '.crt' ]       = 'crt'
            certfiles['flat'][ cn + '.chain.pem' ] = 'chain'
            certfiles['flat'][ cn + '_full.crt' ]  = 'full'

    # define archive contents
    if archive:
        for cn in certnames:
            cn  = prepare_url( cn )
            cnp = os.path.join( 'archive', cn, cdate )
            try:
                certfiles[ cnp ]
            except:
                certfiles[ cnp ] = {}
            certfiles[ cnp ][ 'privkey.pem' ]   = 'pkey'
            certfiles[ cnp ][ 'cert.pem' ]      = 'crt'
            certfiles[ cnp ][ 'chain.pem' ]     = 'chain'
            certfiles[ cnp ][ 'fullchain.pem' ] = 'full'

    # check if writeout should take place
    run_writeout   = True

    # check if FQDN should be handled
    if ( len( limitfqdn ) > 0 ) and ( cert['name'] not in limitfqdn ):
        e_print( 'Skipped "' + cert['name'] + '" since it should be ignored.', COLOR.warn )
    else:
        path_for_check = os.path.join( certs_dir, 'certs', cert['name'], 'fullchain.pem' )

        if os.path.isfile( path_for_check ):

            with open( path_for_check ) as full_open:
                full_file = full_open.read()

            if full_file == cert['full']:
                run_writeout = False

        if run_writeout:
            for parent, sub in certfiles.items():
                for file, c_key in sub.items():

                    file_path = os.path.join( certs_dir, parent, file )

                    # ensure parent folder exists
                    try:
                        directory_path = Path( file_path ).parent
                        os.makedirs( directory_path )
                    except OSError as e:
                        if e.errno != errno.EEXIST:
                            e_print( 'Error creating directory "' + directory_path + '"' )
                            sys.exit( 5 )

                    # write out content
                    with open( file_path , 'w' ) as f:
                        f.write( cert[ c_key ] )

            r_print( 'Certificate extracted for "' + cert['name'] + ('" and SANs "' + '", "'.join( cert['sans'] ) + '"'  if len( cert['sans'] ) > 0 else ''), COLOR.success )
        else:
            e_print( 'Skipped "' + cert['name'] + '" since there was no change on fullchain.', COLOR.warn )

###
## define the Watchdog handler, that triggers the actions with the ACME file
###

class AcmeHandler ( FileSystemEventHandler ) :
    def __init__(self):
        self.last_modified = datetime(2000, 1, 1, 1, 1)

    def on_modified(self, event):
        # the event sometimes seems to be fired twice
        if datetime.now() - self.last_modified > timedelta(seconds=1):
            # event seems to be fired twice sometimes – once for the file and
            # once for the containing directory
            if not event.is_directory:
                event_path = event.src_path
                r_print( 'Change detected in file ' + event_path )
                handle_acme( event_path )
                self.last_modified = datetime.now()

###
## check if all necessary resources exist
###

for d in [ acme_dir, certs_dir ]:
    try:
        os.makedirs( d )
    except OSError as e:
        if e.errno != errno.EEXIST:
            e_print( 'There occured an exception while creating the directory "' + d + '"'  )
            sys.exit( 1 )

if not os.path.isfile( acme_path ):
    e_print( 'There is no ACME file present; cannot proceed.' )
    sys.exit( 2 )

try:
    with open( acme_path ) as acme_open:
        json.load( acme_open )
except:
    e_print( 'Your ACME file seems not to be a valid JSON file; cannot proceed.' )
    sys.exit( 3 )

###
## Check, if there is anything to do right now – and if then do it
###

handle_acme( acme_path )

###
## Running the watch process – and handle changes
###

acme_handler = AcmeHandler()
observer     = Observer()

observer.schedule( acme_handler, acme_path )
observer.start()
try:
    while True:
        time.sleep( 1 )
except KeyboardInterrupt:
    e_print( 'Termination signal received; stopping process', COLOR.warn )
    observer.stop()
observer.join()
