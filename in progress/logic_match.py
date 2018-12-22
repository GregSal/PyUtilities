def logic_match(value):
    truth_values = {'YES', 'Y', 'TRUE', 'T', '1'}
    false_values = {'NO', 'N', 'FALSE', 'F', '0', '-1'}
    value_str = str(value).upper()
    if value_str in truth_values:
        return True
    elif value_str in false_values:
        return False
    return bool(value)
           
print(logic_match(1))
print(logic_match('no'))
