import os, sys
import subprocess
import time
import logging
from datetime import datetime
from os import listdir

import pdb

'''
TODO : * verifier les parametres (fixes en dur, laisser la possibilite de les modifier ?)
    * ... ?
    * TESTER !
'''

class Transformations:
    # Class used to operate transformations to an input env map

    '''
    The output formats for HDR images are :
        * latlong = latitude-longitude map
        * hcross / vcross = horizontal/vertical cross map
        * hstrip / vstrip = horizontal/vertical XXX
        * facelist = set of the 6 faces of a cubemap
        * octant =  light probe (spherical map)
    '''

    def __init__(self, cmft_path, env_path, format_out):
        self.cmft_path = cmft_path    # (String) path to the CMFT command
        self.env_path = env_path    # (String) path to the input env map
        self.format = format_out    # (String) format of the output map
        # Creating a logger to keep track of every operation done
        logDir = "Logs_Transformation"
        if not os.path.exists(logDir):
            os.makedirs(logDir)
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
        logFilePath = os.path.join(logDir, "createDeployDataLog_" + timestamp + ".log")
        self.logger = logging.getLogger()
        self.logger.setLevel("INFO")
        formatter = logging.Formatter('%(asctime)s | %(levelname)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        handler = logging.FileHandler(logFilePath, mode="a", encoding="utf-8")
        handler.setLevel("INFO")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    # PRE-PROCESSING : if the IN env map is spherical, turn it into a latlong
    def preTransfo(self):
        print('Pre-transformation...')
        in_name = os.path.basename(self.env_path)
        in_name = in_name.split('.')[0]
        out_name = in_name + '_result'

        # Generate the map
        self.logger.info("Working on env map " + self.env_path)
        self.logger.info("Generating new map...")
        cmd1 = 'pfsinrgbe ' + self.env_path
        cmd2 = 'pfspanoramic angular+polar -i -o 3'
        cmd3 = 'pfsoutrgbe ' + out_name + '.hdr'
        try:
            self.logger.info("Launching exe with cmd : " + cmd1 + ' | ' + cmd2 + ' | ' + cmd3)
            p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
            p3 = subprocess.Popen(cmd3, stdin=p2.stdout, stdout=subprocess.PIPE)
            p3.communicate()
            self.env_path = out_name + '.hdr'
            self.logger.info("Exe returned error code 0")
            print('Pre-transformation done')
        except subprocess.CalledProcessError as e:
            raise Exception("cmftRelease exe for generate annotation file failed with errorCode " + str(
                e.returncode) + " : " + e.output)

    # Transforming the env map
    def transformMap(self):
        print('Transformation...')
        in_name = os.path.basename(self.env_path)
        in_name = in_name.split('.')[0]
        out_name = in_name + '_' + self.format

        # Generate the map
        self.logger.info("Working on env map " + self.env_path)
        self.logger.info("Generating new map...")
        # TODO cmd
        cmd = self.cmft_path + ' --input ' + self.env_path + ' --filter none'
        # output file parameters
        cmd += ' --outputNum 1 --output0 ' + out_name + ' --output0params hdr,rgbe,' + self.format
        try:
            self.logger.info("Launching exe with cmd : " + cmd)
            subprocess.check_output(cmd)
            self.logger.info("Exe returned error code 0")
            print('Transformation done')
        except subprocess.CalledProcessError as e:
            raise Exception("cmftRelease exe for generate annotation file failed with errorCode " + str(
                e.returncode) + " : " + e.output)

    # Creating an irradiance map from the env map
    def createIrradianceMap(self):
        print('Creating irradiance map...')
        in_name = os.path.basename(self.env_path)
        in_name = in_name.split('.')[0]
        out_name = in_name + '_irr_' + self.format

        # Generate the irradiance map
        self.logger.info("Working on env map " + self.env_path)
        self.logger.info("Generating irradiance map...")
        # irradiance
        cmd = self.cmft_path + ' --input ' + self.env_path + ' --filter irradiance'
        # output file parameters
        cmd += ' --outputNum 1 --output0 ' + out_name + ' --output0params hdr,rgbe,' + self.format
        try:
            self.logger.info("Launching exe with cmd : " + cmd)
            subprocess.check_output(cmd)
            self.logger.info("Exe returned error code 0")
            print('Irradiance map created')
        except subprocess.CalledProcessError as e:
            raise Exception("cmftRelease exe for generate annotation file failed with errorCode " + str(
                e.returncode) + " : " + e.output)

    # Creating a radiance map from the env map
    def createRadianceMap(self):
        print('Creating radiance map...')
        in_name = os.path.basename(self.env_path)
        in_name = in_name.split('.')[0]
        out_name = in_name + '_rad_' + self.format

        # Generate the radiance map
        self.logger.info("Working on env map " + self.env_path)
        self.logger.info("Generating radiance map...")
        # radiance
        cmd = self.cmft_path + ' --input ' + self.env_path + ' --filter radiance'
        cmd += '--srcFaceSize 256 --dstFaceSize 256'
        # mipmap params
        cmd += ' --excludeBase false --mipCount 9 --glossScale 10 --glossBias 1'
        cmd += ' --lightingModel phongbrdf'
        # CPU/GPU/OpenCL parameters
        cmd += '  --numCpuProcessingThreads 4 --useOpenCL true --clVendor anyGpuVendor --deviceType gpu --deviceIndex 0'
        # generate mip map chain after processing
        cmd += ' --generateMipChain false'
        # gamma
        cmd += '  --inputGammaNumerator 1.0 --inputGammaDenominator 1.0 --outputGammaNumerator 1.0' \
               ' --outputGammaDenominator 1.0'
        # output file parameters
        cmd += ' --outputNum 1 --output0 ' + out_name + ' --output0params hdr,rgbe,' + self.format
        try:
            self.logger.info("Launching exe with cmd : " + cmd)
            subprocess.check_output(cmd)
            self.logger.info("Exe returned error code 0")
            print('Radiance map created')
        except subprocess.CalledProcessError as e:
            raise Exception("cmftRelease exe for generate annotation file failed with errorCode " + str(
                e.returncode) + " : " + e.output)

# Main
listeformats = ['latlong', 'hcross', 'vcross', 'hstrip', 'vstrip', 'facelist', 'octant']
format_in = sys.argv[3]
format_out = sys.argv[4]
bad_formats = list(set([format_in, format_out]) - set(listeformats))
if len(bad_formats) == 0:
    transfos = Transformations(sys.argv[1], sys.argv[2], format_out)
    if format_in == 'octant':
        transfos.preTransfo()
    transfos.transformMap()
    transfos.createRadianceMap()
    transfos.createIrradianceMap()
else:
    raise Exception("Bad format(s) : " + ', '.join(bad_formats) + " ; authorized formats : " + ', '.join(listeformats))




