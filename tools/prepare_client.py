#!/usr/bin/env python2
import hashlib
import os
from pandac.PandaModules import *

import argparse
import pytz


parser = argparse.ArgumentParser()
parser.add_argument('--distribution', default='en',
                    help='The distribution string.')
parser.add_argument('--build-dir', default='build',
                    help='The directory in which to store the build files.')
parser.add_argument('--src-dir', default='..',
                    help='The directory of the Toontown Infinite source code.')
parser.add_argument('--server-ver', default='infinite-dev',
                    help='The server version of this build.')
parser.add_argument('--build-mfs', action='store_true',
                    help='When present, the resource multifiles will be built.')
parser.add_argument('--resources-dir', default='../resources',
                    help='The directory of the Toontown Infinite resources.')
parser.add_argument('--config-dir', default='../config/release',
                    help='The directory of the Toontown Infinite configuration files.')
parser.add_argument('--include', '-i', action='append',
                    help='Explicitly include this file in the build.')
parser.add_argument('--exclude', '-x', action='append',
                    help='Explicitly exclude this file from the build.')
parser.add_argument('--vfs', action='append',
                    help='Add this file to the virtual file system at runtime.')
parser.add_argument('modules', nargs='*', default=['otp', 'toontown'],
                    help='The Toontown Infinite modules to be included in the build.')
args = parser.parse_args()

print 'Preparing the client...'

# If necessary, create a directory to store the build files in:
if not os.path.exists(args.build_dir):
    os.mkdir(args.build_dir)
print 'Build directory = {0}'.format(args.build_dir)

# Copy the provided Toontown Infinite modules:


def minify(f):
    """
    Returns the "minified" file data with removed __debug__ code blocks.
    """

    data = ''

    debugBlock = False  # Marks when we're in a __debug__ code block.
    elseBlock = False  # Marks when we're in an else code block.

    # The number of spaces in which the __debug__ condition is indented:
    indentLevel = 0

    for line in f:
        thisIndentLevel = len(line) - len(line.lstrip())
        if ('if __debug__:' not in line) and (not debugBlock):
            data += line
            continue
        elif 'if __debug__:' in line:
            debugBlock = True
            indentLevel = thisIndentLevel
            continue
        if thisIndentLevel <= indentLevel:
            if 'else' in line:
                elseBlock = True
                continue
            if 'elif' in line:
                line = line[:thisIndentLevel] + line[thisIndentLevel+2:]
            data += line
            debugBlock = False
            elseBlock = False
            indentLevel = 0
            continue
        if elseBlock:
            data += line[4:]

    return data


for module in args.modules:
    print 'Writing module...', module
    for root, folders, files in os.walk(os.path.join(args.src_dir, module)):
        outputDir = root.replace(args.src_dir, args.build_dir)
        if not os.path.exists(outputDir):
            os.mkdir(outputDir)
        for filename in files:
            if filename not in args.include:
                if not filename.endswith('.py'):
                    continue
                if filename.endswith('UD.py'):
                    continue
                if filename.endswith('AI.py'):
                    continue
                if filename in args.exclude:
                    continue
            with open(os.path.join(root, filename), 'r') as f:
                data = minify(f)
            with open(os.path.join(outputDir, filename), 'w') as f:
                f.write(data)

# Let's write game_data.py now. game_data.py is a compile-time generated
# collection of data that will be used by the game at runtime. It contains the
# PRC file data, (stripped) DC file, and time zone info.

# First, we need the PRC file data:
configFilePath = os.path.join(args.config_dir, '{0}.prc'.format(args.distribution))
print 'Using configuration file: {0}'.format(configFilePath)
configData = []
with open(configFilePath) as f:
    data = f.readlines()
    for i, line in enumerate(data):
        if 'server-version' in line:
            data[i] = 'server-version {0}'.format(args.server_ver)
            print 'serverVersion = {0}'.format(args.server_ver)
    data += '\n# Virtual file system...\nmodel-path /\n'
    for filepath in args.vfs:
        data += 'vfs-mount {0} /\n'.format(filepath)
    data = '\n'.join(data)
    configData.append(data)

# Next, we need the DC file:
dcData = ''
filepath = os.path.join(args.src_dir, 'astron/dclass')
for filename in os.listdir(filepath):
    if filename.endswith('.dc'):
        fullpath = str(Filename.fromOsSpecific(os.path.join(filepath, filename)))
        print 'Reading {0}...'.format(fullpath)
        with open(fullpath, 'r') as f:
            data = f.read()
            for line in data.split('\n'):
                if 'import' in line:
                    data = data.replace(line + '\n', '')
            dcData += data

# Now, collect our timezone info:
zoneInfo = {}
for timezone in pytz.all_timezones:
    zoneInfo['zoneinfo/' + timezone] = pytz.open_resource(timezone).read()

# Finally, write our data to game_data.py:
print 'Writing game_data.py...'
gameData = '''\
CONFIG = %r
DC = %r
ZONEINFO = %r'''
with open(os.path.join(args.build_dir, 'game_data.py'), 'w') as f:
    f.write(gameData % (configData, dcData.strip(), zoneInfo))


def getDirectoryMD5Hash(directory):
    def _updateChecksum(checksum, dirname, filenames):
        for filename in sorted(filenames):
            path = os.path.join(dirname, filename)
            if os.path.isfile(path):
                fh = open(path, 'rb')
                while True:
                    buf = fh.read(4096)
                    if not buf:
                        break
                    checksum.update(buf)
                fh.close()
    checksum = hashlib.md5()
    directory = os.path.normpath(directory)
    if os.path.exists(directory):
        if os.path.isdir(directory):
            os.path.walk(directory, _updateChecksum, checksum)
        elif os.path.isfile(directory):
            _updateChecksum(
                checksum, os.path.dirname(directory),
                os.path.basename(directory))
    return checksum.hexdigest()


# We have all of the code gathered together. Let's create the multifiles now:
if args.build_mfs:
    print 'Building multifiles...'
    dest = os.path.join(args.build_dir, 'resources')
    if not os.path.exists(dest):
        os.mkdir(dest)
    dest = os.path.realpath(dest)
    os.chdir(args.resources_dir)
    if not os.path.exists('local-patcher.ver'):
        with open('local-patcher.ver', 'w') as f:
            f.write('RESOURCES = {}')
    with open('local-patcher.ver', 'r') as f:
        exec(f.read())
    for phase in os.listdir('.'):
        if not phase.startswith('phase_'):
            continue
        if not os.path.isdir(phase):
            continue
        phaseMd5 = getDirectoryMD5Hash(phase)
        if phase in RESOURCES:
            if RESOURCES[phase] == phaseMd5:
                continue
        filename = phase + '.mf'
        print 'Writing...', filename
        filepath = os.path.join(dest, filename)
        os.system('multify -c -f "{0}" "{1}"'.format(filepath, phase))
        RESOURCES[phase] = phaseMd5
    with open('local-patcher.ver', 'w') as f:
        f.write('RESOURCES = %r' % RESOURCES)

print 'Done preparing the client.'
