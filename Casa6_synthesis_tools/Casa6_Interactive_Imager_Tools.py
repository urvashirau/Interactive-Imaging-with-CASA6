####!/usr/bin/env /export/home/riya/rurvashi/Packages/local_python3/bin/ipython3
##### coding: utf-8

import numpy as np

class ImageCleaner():

    def __init__(self):
        import os
        from casatools import image, synthesisimager, synthesisdeconvolver
        from casatools import synthesisnormalizer, iterbotsink
        from casatasks import casalog
        from casatasks.private.imagerhelpers.input_parameters import ImagerParameters

        self.ia = image()
        self.si = synthesisimager()
        self.sd = synthesisdeconvolver()
        self.sn = synthesisnormalizer()
        self.ib = iterbotsink()

        self.imagename = 'imtry'
        print("Initialize")
        os.system('rm -rf '+self.imagename+'.*')


        self.niter=100
        self.cycleniter=10
        self.itercount=0

        self.finished=False
        self.stopcode=0

        params = ImagerParameters(
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
        
        self.selpars = params.getSelPars()['ms0']
        self.impars = params.getImagePars()['0']
        self.gridpars = params.getGridPars()['0']
        self.decpars = params.getDecPars()['0']
        self.normpars = params.getNormPars()['0']
        self.weightpars = params.getWeightPars()
        self.iterpars = params.getIterPars()


        self.iters=[]
        self.peaks=[]
        self.peaks_in_mask=[]
        self.fluxes=[]
        self.majcycle=[]


    def make_psf(self):
        self.si.makepsf()
        self.sn.gatherpsfweight()  # no-op ? 
        self.sn.dividepsfbyweight()

    def run_major_cycle(self):
        self.sn.dividemodelbyweight()
        self.sn.scattermodel()  # no-op ?
        
        if self.ib != None:
            lastcycle = (self.ib.cleanComplete(lastcyclecheck=True)>0)
        else:
            lastcycle = True
            
        self.si.executemajorcycle(controls={'lastcycle':lastcycle})

        if self.ib != None:
            self.ib.endmajorcycle()

        self.sn.gatherresidual()  # no-op ? 
        self.sn.divideresidualbyweight()
        self.sn.multiplymodelbyweight()

    def has_converged(self):
        self.ib.resetminorcycleinfo()
        initrec = self.sd.initminorcycle()
        self.ib.mergeinitrecord( initrec )
        
        stopflag = self.ib.cleanComplete()
        if( stopflag>0 ):
             stopreasons = ['iteration limit', 'threshold', 'force stop','no change in peak residual across two major cycles', 'peak residual increased by more than 3 times from the previous major cycle','peak residual increased by more than 3 times from the minimum reached','zero mask', 'any combination of n-sigma and other valid exit criterion']
             print("Reached global stopping criterion : " + stopreasons[stopflag-1])

        return (stopflag>0)

    def make_observed_image(self):
        print("Make observed image")

        self.si.selectdata( self.selpars )
        self.si.defineimage( self.impars, self.gridpars )
        self.si.setweighting( **(self.weightpars) )
        self.sn.setupnormalizer( self.normpars )
        self.sd.setupdeconvolution( self.decpars )
        self.ib.setupiteration( self.iterpars )
        
        ## (5) Make the initial images
        self.make_psf()
        self.run_major_cycle()
        
        if self.has_converged() ==True:
            self.stopcode=1

        ## Initialize the mask
        self.sd.setupmask()

        self.ia.open(self.imagename+'.mask')
        mask = self.ia.getchunk()
        mask.fill(0.0)
        shp = self.ia.shape()
        mask[ int(shp[0]*0.05) : int(shp[0]*0.95) ,  int(shp[1]*0.05) : int(shp[1]*0.95), :, : ] = 1.0
        self.ia.putchunk(mask)
        self.ia.close()

#        self.sd.setupmask()


        self.iters=[0]
        self.majcycle=[0]
        self.fluxes=[0.0]

        peak, maskpeak = self.get_peak_residuals()

        self.peaks = [ peak ]
        self.peaks_in_mask = [ maskpeak ]

    def run_minor_cycle(self):
        iterbotrec = self.ib.getminorcyclecontrols()
        self.ib.resetminorcycleinfo()

        iterbotrec['cycleniter'] = self.cycleniter

        #print("Iterbotrec = " + str(iterbotrec))

        exrec = self.sd.executeminorcycle( iterbotrecord = iterbotrec )

        #print("Exrec = " + str(exrec))

        self.ib.mergeexecrecord( exrec )

    def run_deconvolver(self):
        if not self.has_converged():
            self.run_minor_cycle()
            self.run_major_cycle()
        else:
            self.finished=True
            self.stopcode=1

        summ = self.ib.getiterationsummary()
        minarr = summ['summaryminor']

        self.iters= minarr[0,:]
        self.peaks=minarr[1,:]
        self.peaks_in_mask= minarr[1,:]
        self.fluxes = minarr[2,:]

        self.majcycle = summ['summarymajor']

    def run_restore(self):
        if self.finished==False:
            print("Restore the model")
            self.sd.restore()
            self.finished=True
            self.delete_tools()
        else:
            print("Done!")

    def delete_tools(self):
        self.si.done()
        self.sd.done()
        self.sn.done()
        self.ib.done()


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

        ## Send this to the deconvolver
        #self.sd.setupmask()
    
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

    def set_niter(self, cnit):
        self.niter= cnit #np.min( [ cnit, self.niter-self.itercount ] )


#  To run the above....
#from Casa6_Interactive_Imager import ImageCleaner
#imcl = ImageCleaner()
#imcl.make_observed_image()   
#imcl.run_deconvolver()
#imcl.run_restore()
