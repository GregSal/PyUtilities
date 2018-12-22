from Tools.spreadsheet_tools import *


parameter_sheet_info = dict(file_name='Profile Parameter analysis.xlsx',
                          sub_dir=r'Work\electrons',
                          sheet_name='All Profile Parameters')
parameters_sheet = select_sheet(**parameter_sheet_info)
table_info = dict(data_sheet=parameters_sheet, starting_cell='A1',
                  columns='expand', rows='expand', header=1)
b = get_table_range(**table_info)
print('table range\t'+b.address)

#test_sheet_info = dict(file_name='test column.xlsx',
#                          sub_dir=r'Work\electrons',
#                          sheet_name='All Profile Parameters')
#test_sheet = select_sheet(**test_sheet_info)

#data_sheet=test_sheet
#starting_cell='A1'
#columns='expand'
#rows='expand'
#header=0

#start_range = data_sheet.range(starting_cell)
#print('start range\t'+start_range.address)
#end_down = start_range.end('down')
#print('end_down\t'+end_down.address)
#expand_down = start_range.expand('down')
#print('expand_down\t'+expand_down.address)

#table_info = dict(data_sheet=test_sheet, starting_cell='A1',
#            columns='expand', rows='expand', header=0)
#a = get_table_range(**table_info)
#print('table range\t'+a.address)
