''' Fit a two part function containing a quadratic part and a linear part.

Created on Sat Sept 22 2018

@author: Greg
'''
from math import sin, cos, pi
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pylab
from Tools.spreadsheet_tools import select_sheet
from Tools.spreadsheet_tools import load_data_table


def transition_weight(x, centre=10.0, width=6.0):
    '''Calculate a transition weight.
    This function is not working correctly yet.
    '''
    raise NotImplementedError
    lower = centre-width/2
    upper = centre+width/2
    if x < lower:
        weight = (1, 0)
    elif x > upper:
        weight = (0, 1)
    else:
        t = pi*(x-upper)/(2*width)
        w1 = sin(t)**2
        w2 = cos(t)**2
        weight = (w1, w2)
    return weight

def dual_line_point(x, slope1, intercept1, slope2, center, width):
    '''Calculate a 2 slope curve with a transition.
    This function is not working correctly yet.
    '''
    raise NotImplementedError
    intercept2 = center * (slope1 - slope2) + intercept1
    weight = transition_weight(x, center, width)
    y1 = line(x, slope1, intercept1)
    y2 = line(x, slope2, intercept2)
    y = y1*weight[0] + y2*weight[1]
    # a = 'x = {:3.1f} \ty = {:5.1f}\t\tY1 = {:0.1f}\t W1 = {:0.3f}\t\tY2 = {:0.1f}\tW2 = {:0.3f}\t\t Weight sum = {:0.3f}'
    #print(a.format(x, y, y1, weight[0], y2, weight[1], sum(weight)))
    return y


def dual_line_curve(x, slope1, intercept1, slope2, center, width):
    '''calculate dual line for a series
    This function is not working correctly yet.
    '''
    # FIXME dual_line_curve is not working
    raise NotImplementedError
    [dual_line_point(xi, slope1, intercept1, slope2, center, width)
            for xi in x]


def line(x, slope: float, intercept: float) ->float:
    '''Calculate point on a straight line.
    '''
    y = x*slope + intercept
    return y

# %% These are test functions that should be replaced
def load_data():
    '''Load measured data
    '''
    data_sheet = select_sheet(file_name='TR3 R50 Analysis.xlsx',
                                sheet_name='ALL PDD parameters',
                                sub_dir=r'Work\electrons')
    R50_data = load_data_table(data_sheet, index_variables=['SSD', 'Energy'])
    variables = ['EquivSquare', 'R50']
    R50_data = R50_data.loc[('100 cm', '12 MeV'), variables]
    R50_data.sort_values('EquivSquare', inplace=True)
    x = R50_data['EquivSquare']
    yi = R50_data['R50']
    return x, yi

def curve_fit(x, yi):
    # %% call curve fit function
    (popt, pcov) = curve_fit(dual_line_curve, x, yi,
                                p0=(0.25, 3, -0.003, 5, 2))
    (slope1, intercept1, slope2, center, width) = popt
    results_text = 'Optimal parameters are slope1={:g}, intercept1={:g},'
    results_text += 'slope2={:g}, center={:g}, and width={:g}'
    print(results_text.format(slope1, intercept1, slope2, center, width))
    return popt

def plot_fit(x, yi, popt):
    # %% plotting
    yfitted = g(x, *popt)
    pylab.plot(x, yi, 'o', label='data $y_i$')
    pylab.plot(x, yfitted, '-', label='fit $f(x_i)$')
    pylab.xlabel('x')
    pylab.legend()
