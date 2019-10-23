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

    # sum of gradient over entire background (log)
    grad = np.log10(np.sqrt(np.sum(edges_x)**2+np.sum(edges_y)**2) / bkg_image.size)
    # sum of residual of subtraction between the background and the median level of the background (log)
    residual = np.log10(np.sum((bkg_image - np.median(bkg_image))**2) / bkg_image.size)
    
    return grad, residual

def calc_var(df, param):

    center = (df['X_IMAGE'] > 3500) & (df['X_IMAGE'] < 4500) & (df['Y_IMAGE'] > 2600) & (df['Y_IMAGE'] < 3400)
    bottom_left = (df['X_IMAGE'] < 1022) & (df['Y_IMAGE'] < 766)
    top_left = (df['X_IMAGE'] < 1022) & (df['Y_IMAGE'] > 5366)
    bottom_right = (df['X_IMAGE']  > 7154) & (df['Y_IMAGE'] < 766)
    top_right = (df['X_IMAGE'] > 7154) & (df['Y_IMAGE'] > 5366)

    ref_param = df[center][param].median()
    param_list = [df[bottom_left][param].median(), df[top_left][param].median, df[bottom_right][param].median, df[top_right][param].median]
    
    var = 0
    for p in param_list:
        var += ((p/ref_param) - 1)**2
    var = np.sqrt(var)
    var /= len(param_list)

    return var


def gen_feature(filename, goodness, **kwargs):
    from scipy import stats
    from scipy.stats import pearsonr

    df = getdata(filename.split(".")[0]+'_qa.fits', "LDAC_OBJECTS")
    df = pd.DataFrame(np.array(df).byteswap().newbyteorder())
    df['SNR'] = df.FLUX_AUTO / df.FLUXERR_AUTO # define SNR=FLUX/FLUXERR

    sci_photo = getdata(filename, "PHOTOMETRY")
    sci_photo = pd.DataFrame(np.array(sci_photo).byteswap().newbyteorder())
    try:
        templ_photo = getdata(filename, "PHOTOMETRY_TEMPL")
        templ_photo = pd.DataFrame(np.array(templ_photo).byteswap().newbyteorder())
    except:
        print("No PHOTOMETRY_TEMPL in {}".format(filename))

    quality_features = {}
    quality_features['filename'] = filename
    try:
        # ratio of number of detections between science image and template
        quality_features['ST_ratio'] = sci_photo.shape[0]/templ_photo.shape[0] 
    except:
        # NaN if no template in the FITS
        quality_features['ST_ratio'] = np.nan
    
    quality_features['median_fwhm'] = df.FWHM_IMAGE.median()  # median of FWHM_IMAGE over entire image
    quality_features['var_fwhm'] = calc_var(df, "FWHM_IMAGE")  # normalized variance of FWHM_IMAGE between corners and center
    quality_features['median_elong'] = df.ELONGATION.median()  # median of ELONGATION over entire image
    quality_features['var_elong'] = calc_var(df, "ELONGATION")  # normalized variance of ELONGATION between corners and center
    quality_features['median_ellip'] = df.ELLIPTICITY.median()  # median of ELLIPTICITY over entire image
    quality_features['var_ellip'] = calc_var(df, "ELLIPTICITY")  # normalized variance of ELLIPTICITY between corners and center
    quality_features['median_snr'] = df.SNR.median()  # median of SNR over entire image
    quality_features['std_snr'] = df.SNR.std() / df.SNR.median()  # normalized standard deviation of SNR over entire image
    quality_features['var_snr'] = calc_var(df, "SNR") # normalized variance of SNR between corners and center


    # correlation between X_IMAGE and deviation of FWHM
    quality_features['fwhm_xcorr'] = pearsonr(df.X_IMAGE, (df.FWHM_IMAGE-df.FWHM_IMAGE.median())/df.FWHM_IMAGE.std())[0]
    # correlation between Y_IMAGE and deviation of FWHM
    quality_features['fwhm_ycorr'] = pearsonr(df.Y_IMAGE, (df.FWHM_IMAGE-df.FWHM_IMAGE.median())/df.FWHM_IMAGE.std())[0]
    
    # log sum of the background gradient and the subtracted background residual
    quality_features['bkg_gradient'],  quality_features['bkg_residual'] = calc_bkgfluctuation(filename, **kwargs)

    # uniformity of detections over x direction using kstest
    quality_features['x_uniformity'], _ = stats.kstest(df.X_IMAGE/8176, 'uniform')
    # uniformity of detections over y direction using kstest
    quality_features['y_uniformity'], _ = stats.kstest(df.Y_IMAGE/6132, 'uniform')

    quality_features['QA_Score'] = goodness

    return quality_features