from .qa_sex import Sex
import pandas as pd
import os
from .gen_feature import gen_feature

def make_df(filename, goodness, input_csv=None, output_csv="data_set.csv", mode='update', verbose=True):
    if mode == 'update':
        print("Running Sextractor for {}".format(filename))
        sex = Sex.make_config(verbose=verbose)
        sex.run_sex(filename)

    if mode == 'create':
        df = pd.DataFrame(columns=['filename', 'ST_ratio', 'median_fwhm', 'var_fwhm', 
        'median_elong', 'var_elong', 'median_ellip', 'var_ellip', 'median_snr', 'std_snr', 
        'var_snr','fwhm_xcorr', 'fwhm_ycorr', 'bkg_gradient', 'x_uniformity', 'y_uniformity', 'QA_Score'])
    elif mode == 'update':
        if input_csv:
            if os.path.isfile(input_csv):
                df = pd.read_csv(input_csv)
            else:
                raise FileNotFoundError("{} not found!".format(input_csv))
        else:
            raise FileNotFoundError("Input feature table is not given for updating!")
        
        print("Generating features for {}".format(filename))
        features = gen_feature(filename, goodness=goodness)
        df = df.append(features, ignore_index=True)
        os.system("rm -rf {}_qa.fits".format(os.path.splitext(filename)[0]))
        os.system("rm -rf {}_bkg.fits".format(os.path.splitext(filename)[0]))
    else:
        raise KeyError("{} is not a correct mode.".format(mode))

    df.to_csv(output_csv, index=False)

def funpack(filename):
    os.system("mv {} {}.fz".format(filename, filename))
    os.system("funpack {}".format(filename))
    os.system("rm -rf {}.fz".format(filename))
