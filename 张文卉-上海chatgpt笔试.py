import json

file_path = r"D:\Users\Joy\Desktop\annual_report.json"
with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

def fill_table_content(output, table):
    values = []
    headers = []
    prev_col = 0
    prev_row = 0
    multi_row_header = False
    header_rows = []

    # Detect if there is a multi-row header
    for cell in table['table_cells']:
        if cell['start_row'] == 0 and cell['end_row'] > cell['start_row']:
            multi_row_header = True
            header_rows.extend(range(cell['start_row'], cell['end_row'] + 1))
            break  # Exit loop once a multi-row header is found

    # Process each cell in the table
    for line in table['table_cells']:
        # Handling multi-level headers
        if multi_row_header:
            if line['start_row'] in header_rows:
                # Ensure there are enough lists to accommodate multi-row headers
                while len(output['header']) <= line['start_row']:
                    output['header'].append([])
                # Add cell text to the correct header row
                output['header'][line['start_row']].append(line['text'].replace('\n', ''))
        else:
            # Handling single row header
            if line['start_row'] == 0:
                # Create a list for the single row header if it doesn't exist
                if not output['header']:
                    output['header'].append([])
                # Append the cell text to the first (and only) header list
                output['header'][0].append(line['text'].replace('\n', ''))

        # Handling key index and data values
        if line['start_row'] > 0:
            if line['start_col'] == 0 and not line['start_row'] in header_rows:
                output['key_index'].append(line['text'].replace('\n', ''))
            elif line['start_col'] != 0:
                # If this is a new start for the row, add the previous values to output
                if prev_col >= line['start_col']:
                    if values:
                        output['values'].append(values)
                    values = []
                values.append(line['text'].replace('\n', ''))
                prev_col = line['start_col']

    # Ensure the last set of values is added
    if values:
        output['values'].append(values)

    # At the end of processing the table, add the collected header, key_index, and values to output
    # If header processing is independent of the multi-row header logic, it may be set directly without appending
    if not multi_row_header and headers:
        output['header'] = [headers]

        # 将此表格的输出添加到总输出中
    outputs.append(output)

def fill_title_and_unit(output, tables, index):
    if index > 0:
        lines = tables[index - 1]['lines']
        for i, line in enumerate(lines):
            if line['text'].startswith("单位:"):
                output['unit'] = line['text']
                # Handle previous lines for title, skip if '适用' or '不适用'
                for prev_line in reversed(lines[:i]):
                    if '适用' not in prev_line['text'] and '不适用' not in prev_line['text']:
                        output['title'] = prev_line['text']
                        break
                break

def process_tables(current_tables, next_tables):
    # outputs = []
    num_tables = len(current_tables)
    for i, table in enumerate(current_tables):
        if table['type'] == 'table_with_line':  #尝试如果是第一个table_with_line
            if i > 0 and any("年度报告" in line['text'] for line in current_tables[i-1]['lines']):   #如果不加数量是对的但是重复process
                continue  # Skip tables following "年度报告"
            output = {'title': '', 'unit': '', 'header': [], 'key_index': [], 'values': []}
            fill_table_content(output, table)
            fill_title_and_unit(output, current_tables, i)

            # If the current table is second to last and there is a suitable table on next page
            if i == num_tables - 2 and next_tables and len(next_tables) > 1 and (current_tables[-2]['type'] == 'table_with_line' and
            next_tables[1]['type'] == 'table_with_line'):
                fill_table_content(output, next_tables[1])  # Merge content from the second table of the next page

            outputs.append(output)
    return outputs

outputs = []
for i in range(len(data)):
        current_tables = data[f"{i:03d}.png"][0]['result']['tables']

        # Check if there's a next page and prepare next_tables
        next_key = i+1 if i + 1 < len(data) else None
        next_tables = data[f"{next_key:03d}.png"][0]['result']['tables'] if next_key else []

        # Process the current page's tables and account for any continuation onto the next page
        output = process_tables(current_tables, next_tables)
        outputs.append(output)

print(outputs)