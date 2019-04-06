''' Fit a two part function containing a quadratic part and a linear part.

Created on Sat Sept 22 2018

@author: Greg
'''
from typing import List, Dict
from Tools.data_utilities import nearest_step
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from Tools.spreadsheet_tools import select_sheet
from Tools.spreadsheet_tools import load_data_table


def __line(x: float, slope: float, intercept: float) ->float:
    '''Calculate point on a straight line.
    '''
    y = x*slope + intercept
    return y


def __quadratic(x: float, a2: float, a1: float, a0: float) ->float:
    '''Calculate point on a quadratic line.
    $y = a_2x^2 + a_1x + a_0$
    '''
    y = x*x*a2 + x*a1 + a0
    return y


def __ql_q(x: float, centre: float, a2: float, a1: float, a0: float)->float:
    '''Calculate a point on a quadratic + linear curve with a centre point
    using centre, a2, a1 and a0.
    '''
    if x < centre:
        y = quadratic(x, a2, a1, a0)
    else:
        slope2 = 2*a2*centre + a1
        intercept2 = a2*centre*centre + a1*centre + a0 - slope2*centre
        y = line(x, slope2, intercept2)
    return y


def __ql_l(x: float, centre: float, a2: float,
           slope2: float, intercept2: float)->float:
    '''Calculate a point on a quadratic + linear curve with a centre point
    using centre, a2, slope2 and intercept2.
    '''
    if x < centre:
        a1 = slope2 - 2 * a2 * centre
        a0 = intercept2 + a2*centre*centre
        y = __quadratic(x, a2, a1, a0)
    else:
        y = __line(x, slope2, intercept2)
    return y


def extra_parameters(centre: float,
                     a2: float, a1: float = None, a0: float = None,
                     slope2: float = None, intercept2: float = None
                     ) ->Dict[str, float]:
    '''Calculate the missing ql parameters.
    centre and a2 must be given.
    either a1 and a0 or slope2 and intercept2 must be given.
    '''
    if slope2 is None or intercept2 is None:
        slope2 = 2*a2*centre + a1
        intercept2 = a2*centre*centre + a1*centre + a0 - slope2*centre
    elif a1 is None or a0 is None:
        a1 = slope2 - 2 * a2 * centre
        a0 = intercept2 + a2*centre*centre
    ql_parameters = {'a2': a2, 'a1': a1, 'a0': a0, 'centre': centre,
                     'slope2': slope2, 'intercept2': intercept2}
    return ql_parameters


def q_l_point(x: float, parameter_set: Dict[str, float]) ->float:
    '''Calculate a point on a quadratic + linear curve with a centre point.
    centre and a2 must be given.
    either a1 and a0 or slope2 and intercept2 must be given.
    The at the centre point, the quadratic and linear lines and their
    derivatives are equal.
        yq(centre) = yl(centre) and
        yq'(centre) = yl'(centre)
    '''
    ql_parameters = extra_parameters(**parameter_set)
    parameter_names = ['centre', 'a2', 'slope2', 'intercept2']
    parameters = tuple(parameter_set[p] for p in parameter_names)
    y = __ql_l(x, *parameters)
    return y


def q_l_curve(x: List[float], parameter_set: Dict[str, float]) ->float:
    '''calculate a ql curve for a series.
    centre and a2 must be given.
    either a1 and a0 or slope2 and intercept2 must be given.
    The at the centre point, the quadratic and linear lines and their
    derivatives are equal.
        yq(centre) = yl(centre) and
        yq'(centre) = yl'(centre)
    '''
    ql_parameters = extra_parameters(**parameter_set)
    p_names = ['centre', 'a2', 'slope2', 'intercept2']
    param = tuple(ql_parameters[p] for p in p_names)
    y = [__ql_l(xi, *param) for xi in x]
    return y


def q_l_curve_line(x: List[float],  center: float, a2: float,
                   slope2: float, intercept2: float) ->List[float]:
    '''calculate q_l_line for a series giving linear parameters rather
    than a1 and a0.
    '''
    y = [__ql_l(xi, center, a2, slope2, intercept2) for xi in x]
    return y


def ql_fit(x: List[float], yi: List[float],
           initial_values: Dict[str, float] = None) ->Dict[str, float]:
    '''Fit the quadratic-linear model.
    '''
    ql_parameters = extra_parameters(**initial_values)
    p_names = ['centre', 'a2', 'slope2', 'intercept2']
    p0 = tuple(ql_parameters[p] for p in p_names)
    (popt, pcov) = curve_fit(q_l_curve_line, x, yi, p0)
    fit_results = {name: value for (name, value) in zip(p_names, popt)}
    fit_results = extra_parameters(**fit_results)
    return fit_results


def find_ql_fit(data_set: pd.DataFrame, y_name: str, x_name: str,
              starting_param: Dict[str, float]) ->pd.DataFrame:
    '''Return the fit parameters for a given data set.
    '''
    x_values = data_set.index.get_level_values(x_name)
    y_values = data_set[y_name].values
    fit_results = ql_fit(x_values, y_values, initial_values=starting_param)
    return fit_results


def do_ql_fit(data_set: pd.DataFrame, y_name: str, x_name: str,
              starting_param: Dict[str, float]) ->pd.DataFrame:
    '''Return the fit values and residuals for a given data set.
    '''
    x_values = data_set.index.get_level_values(x_name)
    y_values = data_set[y_name].values
    fit_results = ql_fit(x_values, y_values, initial_values=starting_param)
    Fit_values = q_l_curve(x_values, fit_results)
    residuals = y_values - Fit_values
    Fit_index = data_set.index
    fit = pd.DataFrame({'Fit': Fit_values, 'residuals': residuals},
                       index=Fit_index)
    return fit


def fit_ql_curve(raw_data: pd.DataFrame, data_names: Dict[str,str],
                 min_range: float = None, max_range: float = None,
                 step_size: float = 0.1, norm_factor: float = None):
    '''Fit the curve and return fit values in the requested range.
    '''
    x_name = data_names['X']
    y_name = data_names['Y']
    curve = raw_data.groupby(level=x_name).mean()
    raw_x = curve.index.get_level_values(x_name)
    if not min_range:
        min_range = nearest_step(min(raw_x), step_size, towards_zero=False)
    if not max_range:
        max_range = nearest_step(max(raw_x), step_size, towards_zero=True)
    max_range = max_range + step_size/1000
    x_data = np.arange(min_range, max_range, step_size)
    start_centre = max(x_data) - 1
    start_intercept = float(curve.loc[curve.idxmax(),y_name].values)
    initial_values={'centre': start_centre, 'a2': 0,
                    'slope2': 0, 'intercept2': start_intercept}
    fit_results = find_ql_fit(curve, y_name=y_name, x_name=x_name,
                              starting_param=initial_values)
    y_data = q_l_curve(x_data, fit_results)
    y_data = [y/norm_factor for y in y_data]
    return x_data, y_data


def plot_fit(x, yi, fit_results):
    x_max = max(x)
    x_min = min(x)
    x_plotting = np.arange(x_min,x_max, 0.1)
    yfitted = q_l_curve(x_plotting, fit_results)
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(x, yi, 'o', label='data $y_i$')
    ax.plot(x_plotting, yfitted, '-', label='fit $f(x_i)$')
    ax.set_xlabel('Field Size')
    ax.set_ylabel('Value')
    ax.legend()
    plt.show()


def print_results(fit_results):
    '''Formatted print of the fit results.
    '''
    results_text = 'Quadratic parameters: a2={a2:g}, a1={a1:g}, a0={a0:g}\n'
    results_text += 'Linear Parameters: slope2={slope2:g},'
    results_text += 'intercept2={intercept2:g}\n'
    results_text += 'centre point={centre:g}'
    print(results_text.format(**fit_results))


def main():
    '''Demo fit
    '''
    def load_data():
        '''load demo data.
        '''
        data_sheet = select_sheet(file_name='TR3 R50 Analysis.xlsx',
                                  sheet_name='ALL PDD parameters',
                                  sub_dir=r'Work\electrons')
        R50_data = load_data_table(data_sheet,
                                   index_variables=['SSD', 'Energy'])
        variables = ['EquivSquare', 'Linac', 'Applicator', 'Shape',
                     'FieldSize', 'R50']
        R50_data = R50_data.loc[('100 cm', '12 MeV'), variables]
        R50_data.sort_values('EquivSquare', inplace=True)
        x = R50_data['EquivSquare']
        yi = R50_data['R50']
        return x, yi

    x, yi = load_data()
    fit_results = ql_fit(x, yi, initial_values={'a2': -0.08, 'a1': 0.97, 'a0': 3.66, 'centre': 7})
    print_results(fit_results)
    plot_fit(x, yi, fit_results)


if __name__ == '__main__':
    main()
