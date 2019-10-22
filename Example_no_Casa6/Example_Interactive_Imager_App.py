####!/usr/bin/env /export/home/riya/rurvashi/Packages/local_python3/bin/ipython3
##### coding: utf-8

#from casatools import image 
#ia = image()
#from Interactive_Clean_Casa6_Demo import ia

import numpy as np

from Example_Interactive_Imager import ImageCleaner
    
imcl = ImageCleaner()
imcl.make_observed_image()

#################################################
#################################################
#################################################

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    
    html.Div(children=[
        dcc.Graph(id='masked_res'),
        
#        html.Button('Start', id='start_button'),

        html.Div([ 
            html.Button('Continue', id='cont_button'),
            dcc.Input(id='input_cycleniter', type='number', value=20),
            html.Div(id='cycleniter_message',
                     children='Cycleniter ')
        ], style={'width': '40%', 'display': 'inline-block','vertical-align':'top'}),

        html.Button('Stop', id='stop_button'),
], 
             style={'width': '50%', 'display': 'inline-block','vertical-align':'top','padding':'20px'}),
    html.Div(children=[
        dcc.Graph(id='iter_plot') ], 
             style={'width': '40%', 'display': 'inline-block','vertical-align':'top'})

]
)

@app.callback(
[ Output('cycleniter_message', 'children') ],
[ Input( 'input_cycleniter', 'value') ]
)
def update_output( cycleniter ):
    if cycleniter != None:
        imcl.set_cycleniter( int(cycleniter) )
    else:
        print ('cycleniter is None. No change')
    return ['Cycleniter : {}'.format( imcl.get_cycleniter() )]

@app.callback(
    [Output('masked_res', 'figure'),
     Output('iter_plot', 'figure')],
    [   Input('cont_button', 'n_clicks'),
        Input('stop_button', 'n_clicks'),
        Input('masked_res','selectedData')
   ]
)
def update_figure(cont_clicks, stop_clicks, selected_data):
    
    ctx = dash.callback_context
    #print('Trig : ' + str( ctx.triggered) )
    #print("Start : " + str(start_clicks) + " Stop : "+ str(stop_clicks) + " Cont : " + str(cont_clicks))

    residual, mask = imcl.get_residual_and_mask()

    if ctx.triggered[0]['prop_id'].count('selectedData')>0:
        if selected_data != None:
            if 'range' in selected_data.keys() :
                #print(selected_data['range'])
                imcl.update_mask( selected_data['range'] )
                residual,mask = imcl.get_residual_and_mask()
            else:
                print("Only box region selection is currently supported")

    if ctx.triggered[0]['prop_id'].count('button')>0:
    
        ## Only once at the beginning
#        if start_clicks==1 and cont_clicks==None and stop_clicks==None and imcl.get_stopcode()==0:
#            imcl.make_observed_image()
#            residual, mask = imcl.get_residual_and_mask()

        ## Until you stop, or the stopcode goes to 1
        if stop_clicks==None and cont_clicks!=None and imcl.get_stopcode()==0:
            imcl.run_deconvolver()
            residual, mask = imcl.get_residual_and_mask()
            
        if stop_clicks==1 or  imcl.get_stopcode()==1:
            imcl.run_restore()


    traces=[]
    traces.append( go.Scatter(y=[None]) )
    traces.append( go.Heatmap(z=np.transpose(residual), 
                              showscale=False,
                              colorscale='Blackbody') )
    traces.append( go.Contour(z=np.transpose(mask), 
                              contours_coloring='lines',
                              line_width=4, 
                              showscale=False,
                              colorscale='Jet',
                              contours=dict(start=0.1,end=1.1,size=2)
                          ))

    iters, peaks, peaks_in_mask, majcycle = imcl.get_iter_plot()

    traces_plot=[]
    traces_plot.append( go.Scatter(x=iters, y=peaks, 
                                   mode='lines+markers', 
                                   name='Full Image' ))
    traces_plot.append( go.Scatter(x=iters, y=peaks_in_mask, 
                                   mode='lines+markers', 
                                   name='Within Mask' ))
    for it in majcycle:
        showlegend = False
        if it==majcycle[0]:
            showlegend=True
        traces_plot.append( go.Scatter(x=[it,it], y=[0, peaks[0]], 
                                       mode='lines' ,
                                       name='Major cycles',
                                       line=dict(color='grey',dash='dash'),
                                       showlegend=showlegend) )
    
    return [
        {
            'data': traces,
            'layout': go.Layout(
                xaxis={'title': 'RA (pix)'},
                yaxis={'title': 'DEC (pix)'},
                title="RESIDUAL IMAGE WITH MASK",
                width = 500, height = 500,
                autosize = True,
                dragmode = 'select',
                hovermode=False
            )} ,
        {
            'data': traces_plot,
            'layout': go.Layout(
                xaxis={'title': 'Iteration Count', 'range':[-0.5,imcl.get_niter()]},
                yaxis={'title': 'Peak Residual'},
                title="Convergence Plot : Peak Residual vs Iteration Number",
                width = 600, height = 500,
                autosize = True
            )} 
    ]
    



#### Start the App

if __name__ == '__main__':
    app.run_server(debug=True)
 
