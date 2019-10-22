####!/usr/bin/env /export/home/riya/rurvashi/Packages/local_python3/bin/ipython3
##### coding: utf-8

import numpy as np

class ImageCleaner():

    def __init__(self):
        from casatasks.private.imagerhelpers.imager_base import PySynthesisImager
        from casatasks.private.imagerhelpers.input_parameters import ImagerParameters
        from casatools import image 
        from casatasks import casalog
        import os

        self.ia = image()

        self.imagename = 'imtry'
        self.niter=100
        self.cycleniter=10
        self.itercount=0

        print("Initialize")

        os.system('rm -rf '+self.imagename+'.*')
    
        ## (2) Set up Input Parameters

        paramList = ImagerParameters(
            msname ='point.ms',
            spw='0:10',
            imagename=self.imagename,
            imsize=100,
            cell='5.0arcsec',
            specmode='mfs',
            gridder='standard',
            niter=self.niter,
            cycleniter=self.cycleniter,
            loopgain=0.05,
            deconvolver='hogbom'
        )

        ## (3) Construct the PySynthesisImager object, with all input parameters

        self.imager = PySynthesisImager(params=paramList)

        self.finished=False
        self.stopcode=0

        self.iters=[]
        self.peaks=[]
        self.peaks_in_mask=[]
        self.fluxes=[]
        self.majcycle=[]

    def get_image(self, imname=''):
        self.ia.open(imname)
        pix = self.ia.getchunk()[:,:,0,0]
        self.ia.close()
        return pix

    def get_residual_and_mask(self):
        return self.get_image(self.imagename+'.residual'), self.get_image( self.imagename+'.mask')

    def get_peak_residuals(self):
        residual = self.get_image(self.imagename+'.residual')
        mask = self.get_image(self.imagename+'.mask')
        return np.max(residual),  np.max(residual*mask)

    def get_stopcode(self):
        return self.stopcode

    def get_iter_plot(self):
        return self.iters, self.peaks, self.fluxes, self.majcycle

    def get_niter(self):
        return self.niter

    def get_cycleniter(self):
        return self.cycleniter
        
    def set_cycleniter(self, cnit):
        self.cycleniter= cnit #np.min( [ cnit, self.niter-self.itercount ] )

    def make_observed_image(self):
        print("Make observed image")

        ## Initialize modules major cycle modules
        self.imager.initializeImagers()
        self.imager.initializeNormalizers()
        self.imager.setWeighting()
        
        ## Init minor cycle modules
        self.imager.initializeDeconvolvers()
        self.imager.initializeIterationControl()
        
        ## (5) Make the initial images
        self.imager.makePSF()
        #self.imager.makePB()
        self.imager.runMajorCycle() # Make initial dirty / residual image
        
        ## (6) Make the initial clean mask
        if self.imager.hasConverged() ==True:
            self.stopcode=1
        self.imager.updateMask()

        ## Initialize the mask to zeros.
        self.ia.open(self.imagename+'.mask')
        mask = self.ia.getchunk()
        mask.fill(0.0)
        shp = self.ia.shape()
        mask[ int(shp[0]*0.05) : int(shp[0]*0.95) ,  int(shp[1]*0.05) : int(shp[1]*0.95), :, : ] = 1.0
        self.ia.putchunk(mask)
        self.ia.close()

        self.iters=[0]
        self.majcycle=[0]
        self.fluxes=[0.0]

        peak, maskpeak = self.get_peak_residuals()

        self.peaks = [ peak ]
        self.peaks_in_mask = [ maskpeak ]

    def run_deconvolver(self):
        if not self.imager.hasConverged():
            self.imager.runMinorCycle()
            self.imager.runMajorCycle()
        else:
            self.finished=True
            self.stopcode=1

        summ = self.imager.getSummary()
#        print(summ)

        minarr = summ['summaryminor']

        self.iters= minarr[0,:]
        self.peaks=minarr[1,:]
        self.peaks_in_mask= minarr[1,:]
        self.fluxes = minarr[2,:]

        self.majcycle = summ['summarymajor']

    def run_restore(self):
        if self.finished==False:
            print("Restore the model")
            self.imager.restoreImages()
            self.imager.deleteTools()
            self.finished=True
        else:
            print("Done!")

    def update_mask(self, xyrange={}, add_erase='add'):
        xmin = int( np.min( xyrange['x'] ) )
        xmax = int( np.max( xyrange['x'] ) )
        ymin = int( np.min( xyrange['y'] ) )
        ymax = int( np.max( xyrange['y']) )

        self.ia.open(self.imagename+'.mask')
        pix = self.ia.getchunk()
        if add_erase=='add':
            pix[ xmin:xmax, ymin:ymax, 0,0 ] = 1.0
        else:
            pix[ xmin:xmax, ymin:ymax, 0,0 ] = 0.0
            
        self.ia.putchunk( pix )
        self.ia.close()
    


#  To run the above....
#from Casa6_Interactive_Imager import ImageCleaner
#imcl = ImageCleaner()
#imcl.make_observed_image()   
#imcl.run_deconvolver()
#imcl.run_restore()
