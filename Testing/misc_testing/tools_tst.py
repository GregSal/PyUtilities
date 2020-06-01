from spreadsheet_tools import *
from data_utilities import *

test_worksheet_info = dict(file_name='Profile Parameter analysis.xlsx',
                     sub_dir=r'Work\electrons',
                     sheet_name='TR3 square Profile Parameters')
test_data_sheet = select_sheet(**test_worksheet_info)

table = dict(data_sheet=test_data_sheet, starting_cell='B3',
                  columns='expand', rows='expand', header=1)

value_list = ['SSD', 'Start position [De]', 'End position [De]',
              'Field size inline', 'Field size crossline', 'Gantry angle',
              'Collimator angle', 'Flatness', 'Symmetry', 'FieldWidth',
              'Penumbra', 'Center']
name_swap = [('Radiation device', 'Linac'),
             ('Ds', 'SurfaceDose'),
             ('Dmax', 'MaxDose'),
             ('Rp', 'R_p'),
             ('Rt', 'R_t'),
             ('E0', 'E_0'),
             ('Start position [De]', 'scan_length')]


# Done to Here
rename_variable(data_sheet, name_swap)

field_size_parameters(data_sheet, top_cell=top_cell,
                          circle_default=False)
int_applicator(data_sheet)

SSD_to_str(data_sheet)



profile_table = dict(file_name='Profile Parameter analysis.xlsx',
                     sub_dir=r'Work\electrons', starting_cell='B3',
                     sheet_name=None, columns='expand')
sheet_names = ['TR3 square Profile Parameters',
               'TR3 circle Profile Parameters',
               'TR2 Profile Parameters']

########
# Test range
########C:\Users\Greg\OneDrive - Queen's University\
from spreadsheet_tools import *


parameter_sheet_info = dict(
    file_name='test column.xlsx',
    sub_dir=r'Python\Projects\EclipseRelated\BeamDataTools\Testing',
    sheet_name='All Profile Parameters')
parameters_sheet = select_sheet(**parameter_sheet_info)
table_info = dict(data_sheet=parameters_sheet, starting_cell='A1',
                  columns='expand', rows='expand', header=1)
b = get_table_range(**table_info)
print('table range\t'+b.address)

test_sheet_info = dict(
    file_name='test column.xlsx',
    sub_dir=r'Python\Projects\EclipseRelated\BeamDataTools\Testing',
    sheet_name='test column')
test_sheet = select_sheet(**test_sheet_info)

data_sheet=test_sheet
starting_cell='A1'
columns='expand'
rows='expand'
header=0

start_range = data_sheet.range(starting_cell)
print('start range\t'+start_range.address)
end_down = start_range.end('down')
print('end_down\t'+end_down.address)
expand_down = start_range.expand('down')
print('expand_down\t'+expand_down.address)

test_sheet_info = dict(
    file_name='test column.xlsx',
    sub_dir=r'Python\Projects\EclipseRelated\BeamDataTools\Testing',
    sheet_name='All Profile Parameters')
test_sheet = select_sheet(**test_sheet_info)
table_info = dict(data_sheet=test_sheet, starting_cell='A1',
            columns='expand', rows='expand', header=0)
a = get_table_range(**table_info)
print('table range\t'+a.address)

######### End of test range #########

# %% Doc strings good to here



# %%
def __main__():
    worksheet = select_sheet(file_name='Profile Analysis.xlsx',
                             sub_dir=r'Work\electrons',
                             sheet_name='Data')
    field_size_list = get_data_column(worksheet, variable='FieldSize')
    field_width_list = get_data_column(worksheet, variable='FieldWidth')
    direction_list = get_data_column(worksheet, variable='Direction')
    width_ratio_list = list()
    for (field_size, field_width, direction) in zip(field_size_list,
                                                    field_width_list,
                                                    direction_list):
        width_ratio = get_field_size_ratio(field_size, field_width, direction)
        width_ratio_list.append(width_ratio)
    append_data_column(worksheet, 'Width Ratio', width_ratio_list)
    format_data_column(worksheet, variable='Width Ratio', style='0.0%')
    worksheet = select_sheet(file_name='Profile Analysis.xlsx',
                             sub_dir=r'Work\electrons',
                             sheet_name='Data')
    rdf_data = load_data_table(worksheet, starting_cell='A2')

    rdf_data = merge_columns(rdf_data,
                             columns=['Measured', 'Eclipse', 'Fit'],
                             data_column='RDF',
                             index_column='Source')
    index = ['Source', 'SSD', 'Energy', 'Applicator', 'Shape',
             'FieldSize', 'EqSq']
    rdf_data.set_index(index, inplace=True)
    worksheet = append_data_sheet(worksheet.book,
                                  sheet_name='RDF Data Stacked',
                                  data_table=rdf_data)
    format_data_column(worksheet, variable='RDF', style='0.000')
    format_data_column(worksheet, variable='EqSq', style='0.00')
    field_size_list = get_data_column(worksheet, variable='FieldSize')
    field_width_list = get_data_column(worksheet, variable='FieldWidth')
    width_ratio_list = list()
    for (field_size, field_width) in enumerate(field_size_list,
                                               field_width_list):
        width_ratio = field_width/field_size
        width_ratio_list.append(width_ratio)
    append_data_column(worksheet, 'Width Ratio', width_ratio_list)
    format_data_column(worksheet, variable='Width Ratio', style='0.0%')

