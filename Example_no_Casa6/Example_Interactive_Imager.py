####!/usr/bin/env /export/home/riya/rurvashi/Packages/local_python3/bin/ipython3
##### coding: utf-8

import numpy as np

## A fake imager that creates an image of noise plus a few spots.
## The 'deconvolution' is simply an iterative cutting down of the brightest peak in the image. 
class ImageCleaner():

    def __init__(self):
        print("Initialize")
        
        ## Iteration control and array initialization
        self.N = 100
        self.residual = np.ones( (self.N, self.N) )
        self.mask = np.zeros( (self.N, self.N) )
        self.stopcode=0 # Continue
        self.niter=200
        self.itercount=0
        self.cycleniter=20
        self.finished=False

        ## Iteration and convergence summary holders
        self.iters=[]
        self.peaks=[]
        self.peaks_in_mask=[]
        self.majcycle=[]

    ## Several accessor methods
    def get_residual_and_mask(self):
        return self.residual, self.mask

    def get_stopcode(self):
        return self.stopcode

    def get_iter_plot(self):
        return self.iters, self.peaks, self.peaks_in_mask, self.majcycle

    def get_cycleniter(self):
        return self.cycleniter

    def get_niter(self):
        return self.niter
        
    ## Set an iteration control parameter to be used in the next run_deconvolver call
    def set_cycleniter(self, cnit):
        self.cycleniter= np.min( [ cnit, self.niter-self.itercount ] )

    ## Update mask pixels from user interaction
    def update_mask(self, xyrange={}):
        xmin = int( np.min( xyrange['x'] ) )
        xmax = int( np.max( xyrange['x'] ) )
        ymin = int( np.min( xyrange['y'] ) )
        ymax = int( np.max( xyrange['y']) )
        
        self.mask[ xmin:xmax, ymin:ymax ] = 1.0


    ## Make the initial observed image.  
    def make_observed_image(self):
        print("Make observed image")
        ## Random noise plus a few fat spots
        self.residual = np.random.randn(self.N,self.N) # + np.random.poisson(size=(self.N,self.N))
        locs = np.random.uniform(low=10,high=self.N-10,size=(2,5)) # locs of 5 'sources'
        for ii in range(0,5): # Make 5 'sources' that are 4 pixels each...
            self.residual [ int( locs[0,ii] ) , int( locs[1,ii] ) ] = self.residual [ int( locs[0,ii] ) , int( locs[1,ii] ) ] +  np.random.uniform(low=10,high=20)
            self.residual [ int( locs[0,ii] )+1 , int( locs[1,ii] )+1 ] = self.residual [ int( locs[0,ii] ) , int( locs[1,ii] ) ] +  np.random.uniform(low=10,high=20)
            self.residual [ int( locs[0,ii] )+1 , int( locs[1,ii] ) ] = self.residual [ int( locs[0,ii] ) , int( locs[1,ii] ) ] +  np.random.uniform(low=10,high=20)
            self.residual [ int( locs[0,ii] ) , int( locs[1,ii] )+1 ] = self.residual [ int( locs[0,ii] ) , int( locs[1,ii] ) ] +  np.random.uniform(low=10,high=20)

        ## Set an initial inner-quarter mask
        self.mask [ int(self.N/4):int(3*self.N/4) , int(self.N/4):int(3*self.N/4) ] = 1.0

        ## Initialize the iteration summary info with starting values
        self.iters.append( self.itercount )
        self.peaks.append( np.max(self.residual) )
        self.majcycle.append(self.itercount)
        self.peaks_in_mask.append(  np.max(self.residual * self.mask)    ) 

    ## Run the 'deconvolution'
    def run_deconvolver(self):
        for ii in range(0,self.cycleniter):   ## Equivalent of minor cycle iterations
            masked_residual = self.residual * self.mask
            mval = np.max(masked_residual)
            self.residual[ masked_residual == mval ] = mval*0.7   # Just set the peak to 70% the peak. Similar to 'loopgain=0.3' in tclean. 
            self.itercount = self.itercount+1

            ## Record convergence information
            self.iters.append( self.itercount )
            self.peaks.append( np.max(self.residual) )
            self.peaks_in_mask.append(  np.max(self.residual * self.mask)    ) 

            ## Check for stopping criteria
            if self.itercount >= self.niter:
                self.stopcode=1  # time to stop
                break

        ## Record when minor cycles exited (i.e. an imaginary major cycle happens here)
        self.majcycle.append(self.itercount)
        print("Deconvolved for " + str(self.itercount) + " iterations")

    ## Done with deconvolution. Restore. This is last step after which no iterations happen
    def run_restore(self):
        if self.finished==False:
            print("Restore the model")
            self.finished=True
        else:
            print("Done!")

###########################################################
    
