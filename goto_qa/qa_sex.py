import os
from . import config

class Sex():
    def __init__(self, conf_args, config_fn, param_fn, gauss_filter):
        self.conf_args = conf_args
        self.config_fn = config_fn
        self.param_fn = param_fn
        self.gauss_filter = gauss_filter
        
    @classmethod
    def make_config(cls, thresh='3', verbose=True):
        # create default config file
        os.system("{} -d > .qa.sex".format(getattr(config, 'sex_cmd')))


        # create config arguments
        conf_args = {}

        #---------Catalog---------#
        conf_args['CATALOG_TYPE'] = 'FITS_LDAC'
        conf_args['PARAMETERS_NAME'] = '.qa.param'

        #---------Extraction---------#    
        conf_args['DETECT_MINAREA'] = '2'
        conf_args['DETECT_MAXAREA'] = '75'
        conf_args['DETECT_THRESH'] = thresh
        conf_args['ANALYSIS_THRESH'] = thresh
        conf_args['FILTER'] = 'N'
        conf_args['FILTER_NAME'] = '.gauss_1.5_3x3.conv'
        conf_args['FILTER_THRESH'] = '3'
        conf_args['DEBLEND_MINCONT'] = '0.001'

        #---------Extraction---------#
        conf_args['PHOT_APERTURES'] = '5'
        conf_args['PHOT_AUTOPARAMS'] = '1.5,2.5'
        conf_args['SATUR_LEVEL'] = '52000.0'
        conf_args['PIXEL_SCALE'] = '1.24'

        #---------Background---------#
        conf_args['BACK_SIZE'] = '128'
        conf_args['BACKPHOTO_TYPE'] = 'LOCAL'
        conf_args['BACKPHOTO_THICK'] = '24'

        #---------Check Image---------#
        conf_args['CHECKIMAGE_TYPE'] = 'BACKGROUND'
        if verbose:
            conf_args['VERBOSE_TYPE'] = 'NORMAL'
        else:
            conf_args['VERBOSE_TYPE'] = 'QUIET'


        # create gaussian filter
        f = open('.gauss_1.5_3x3.conv', 'w')
        print("""CONV NORM
# 3x3 convolution mask of a gaussian PSF with FWHM = 1.5 pixels.
0.109853 0.300700 0.109853 
0.300700 0.823102 0.300700
0.109853 0.300700 0.109853""", file=f)
        f.close()

        # create param file
        params = ['X_IMAGE', 'Y_IMAGE', 'ELONGATION', 'ELLIPTICITY', 
                  'FWHM_IMAGE','FLUX_AUTO','FLUXERR_AUTO']
        f = open('.qa.param', 'w')
        print('\n'.join(params), file=f)
        f.close()
        
        return cls(conf_args, '.qa.sex', '.qa.param', '.gauss_1.5_3x3.conv')
    
    def get_cmd(self, filename):
        cmd = ' '.join([format(getattr(config, 'sex_cmd')), filename+'[0]', '-c {} '.format(self.config_fn)])
        self.conf_args['CATALOG_NAME'] = '_'.join([filename.split(".")[0], 'qa.fits'])
        self.conf_args['CHECKIMAGE_NAME'] = '_'.join([filename.split(".")[0], 'bkg.fits'])
        args = [''.join(['-', key, ' ', str(self.conf_args[key])]) for key in self.conf_args]
        cmd += ' '.join(args)
        self.cmd = cmd
        
    def config_cleanup(self):
        conf_files = [self.config_fn, self.param_fn, self.gauss_filter]
        for f in conf_files:
            os.remove(f)
    
    def run_sex(self, filename):
        self.get_cmd(filename)
        os.system(self.cmd)
        self.config_cleanup()