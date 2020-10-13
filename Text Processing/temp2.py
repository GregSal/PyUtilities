import Text_Processing as tp

parser = tp.define_fixed_width_parser(widths=10)
test_text = [
                'Dose [cGy] Ratio of Total Structure Volume [%]',
                '         0                       100',
                '         1                       100',
                '         2                       100',
                '         3                       100',
                '         4                       100',
                '         5                       100',
                '      3667              4.23876e-005',
                '      3668              2.87336e-005',
                '      3669              1.50797e-005',
                '      3670               1.4257e-006',
]

processed_lines = [parser(line) for line in test_text]
output = tp.to_dataframe(processed_lines, header=True)
print(output)
