from astropy.io.fits import getdata
import pandas as pd
import numpy as np

def calc_bkgfluctuation(filename, scale=0.003):
    from PIL import Image
    from skimage import filters

    bkg_fn = filename.split(".")[0] + "_bkg.fits"
    bkg_img = getdata(bkg_fn, 0)
    bkg_img = np.array(bkg_img).byteswap().newbyteorder()
    bkg_image = Image.fromarray(bkg_img)
    factor = scale
    width = int(bkg_image.size[0] * factor)
    height = int(bkg_image.size[1] * factor)
    bkg_image = bkg_image.resize((width, height), Image.ANTIALIAS)    # best down-sizing filter
    bkg_image = np.array(bkg_image)
    
    edges_x = filters.sobel_h(bkg_image)
    edges_y = filters.sobel_v(bkg_image)
    grad = np.sqrt(np.sum(edges_x)**2+np.sum(edges_y)**2) / bkg_image.size
    
    residual = np.sum((bkg_image - np.median(bkg_image))**2) / bkg_image.size
    
    return grad, residual


def gen_feature(filename, goodness, **kwargs):
    from scipy import stats
    from scipy.stats import pearsonr

    df = getdata(filename.split(".")[0]+'_qa.fits', "LDAC_OBJECTS")
    df = pd.DataFrame(np.array(df).byteswap().newbyteorder())
    df['SNR'] = df.FLUX_AUTO / df.FLUXERR_AUTO

    quality_features = {}
    quality_features['filename'] = filename
    quality_features['sci_ndet'] = df.shape[0]
    quality_features['std_elong'] = df.ELONGATION.std()
    quality_features['std_ellip'] = df.ELLIPTICITY.std()
    quality_features['mean_fwhm'] = df.FWHM_IMAGE.mean()
    quality_features['std_fwhm'] = df.FWHM_IMAGE.std() / df.FWHM_IMAGE.mean()
    quality_features['fwhm_xcorr'] = pearsonr(df.X_IMAGE, (df.FWHM_IMAGE-df.FWHM_IMAGE.median())/df.FWHM_IMAGE.std())[0]
    quality_features['fwhm_ycorr'] = pearsonr(df.Y_IMAGE, (df.FWHM_IMAGE-df.FWHM_IMAGE.median())/df.FWHM_IMAGE.std())[0]
    quality_features['mean_snr'] = df.SNR.mean()
    quality_features['std_snr'] = df.SNR.std() / df.SNR.mean()
    quality_features['bkg_gradient'],  quality_features['bkg_residual'] = calc_bkgfluctuation(filename, **kwargs)
    quality_features['ks_stat_x'], quality_features['ks_pval_x'] = stats.kstest(df.X_IMAGE/8176, 'uniform')
    quality_features['ks_stat_y'], quality_features['ks_pval_y'] = stats.kstest(df.Y_IMAGE/6132, 'uniform')
    quality_features['QA_Score'] = goodness

    return quality_features