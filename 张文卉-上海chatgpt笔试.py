import json

file_path = r"D:\Users\Joy\Desktop\annual_report.json"
with open(file_path, "r", encoding="utf-8") as read_file:
    data = json.load(read_file)


def fill_table_content(output, table):
    values = []
    prev_col = 0
    multi_row_header = False
    header_rows = []

    # First, detect if there is a multi-row header
    for cell in table["table_cells"]:
        if cell["start_row"] == 0 and cell["end_row"] > cell["start_row"]:
            multi_row_header = True
            header_rows.extend(range(cell["start_row"], cell["end_row"] + 1))
            break  # Exit loop once a multi-row header is found

    # Process each cell in the table
    for line in table["table_cells"]:
        # Handle multi-row headers
        if multi_row_header:
            if line["start_row"] in header_rows:
                while len(output["header"]) <= line["end_row"]:
                    output["header"].append([])

                for header_row in range(line["start_row"], line["end_row"] + 1):
                    while len(output["header"][header_row]) <= line["end_col"]:
                        output["header"][header_row].append("")
                    for header_col in range(line["start_col"], line["end_col"] + 1):
                        output["header"][header_row][header_col] = line["text"].replace(
                            "\n", ""
                        )
        else:
            # Handling single row header
            if line["start_row"] == 0:
                if not output["header"]:
                    output["header"].append([])
                output["header"][0].append(line["text"].replace("\n", ""))

        # Handle key index and data values
        if (
            line["start_row"] > 0
            and line["start_col"] == 0
            and not line["start_row"] in header_rows
        ):
            output["key_index"].append(line["text"].replace("\n", ""))
        elif line["start_row"] > 0 and line["start_col"] != 0:
            if prev_col >= line["start_col"]:
                if values:  # Only append if values are non-empty
                    output["values"].append(values)
                values = []
            values.append(line["text"].replace("\n", ""))
            prev_col = line["start_col"]

    # Ensure the last set of values is added
    if values:
        output["values"].append(values)


def fill_title_and_unit(output, tables, index):
    if index > 0:
        lines = tables[index - 1]["lines"]
        found_unit = False
        unit_parts = []  # store unit 单位 币种
        possible_titles = []  # collect all possible headers

        # search reversely to find unit
        for line in reversed(lines):
            # collect all lines that is not "适用"and"不适用" to be possible titles
            if "适用" not in line["text"] and "不适用" not in line["text"]:
                possible_titles.append(line["text"])

            # check if it contains unit
            if "单位:" in line["text"] or "币种:" in line["text"]:
                unit_parts.append(line["text"])
                found_unit = True

        # if found unit, combine units to handle unit that are in different text
        if found_unit:
            output["unit"] = " ".join(reversed(unit_parts))
            if possible_titles:
                # filter title, don't contain unit
                filtered_titles = [
                    title
                    for title in possible_titles
                    if "单位:" not in title and "币种:" not in title
                ]
                if filtered_titles:
                    output["title"] = filtered_titles[0] #title is the first text that are not unit

        # unit not found
        elif possible_titles:
            output["title"] = possible_titles[0]  # first text in before table

def process_tables(current_tables, next_tables):
    outputs = []
    num_tables = len(current_tables)
    for i, table in enumerate(current_tables):
        if table["type"] == "table_with_line":
            if (
                i == 1
            ):  # The table is at index 1, which means it's the second table or content block on the page
                # get the first table block on the page
                previous_table_lines = [
                    line["text"] for line in current_tables[0]["lines"]
                ]
                if (
                    len(previous_table_lines) == 1
                    and "2021年年度报告" in previous_table_lines[0]
                ):
                    # Skip processing this table as it's the header of the page
                    continue
            output = {
                "title": "",
                "unit": "",
                "header": [],
                "key_index": [],
                "values": [],
            }
            # process normal table
            fill_table_content(output, table)
            fill_title_and_unit(output, current_tables, i)

            # process cross-page table
            # If the current table is second to last and there is a suitable table on next page
            if (
                i == num_tables - 2
                and next_tables
                and len(next_tables) > 1
                and (
                    current_tables[-2]["type"] == "table_with_line"
                    and next_tables[1]["type"] == "table_with_line"
                )
                # only merge if next page's title only have page headers before
                and len(next_tables[0]["lines"]) == 1 
                and "2021年年度报告" in next_tables[0]["lines"][0]["text"]
            ):
                fill_table_content(
                    output, next_tables[1]
                )  # Merge content from the second table of the next page

            outputs.append(output)
    return outputs


outputs = []
for i in range(len(data)):
    current_tables = data[f"{i:03d}.png"][0]["result"]["tables"]

    # Check if there's a next page and prepare next_tables
    next_key = i + 1 if i + 1 < len(data) else None
    next_tables = data[f"{next_key:03d}.png"][0]["result"]["tables"] if next_key else []

    # Process the current page's tables and account for any continuation onto the next page
    output = process_tables(current_tables, next_tables)
    outputs.extend(output)

print(outputs)


# Edge case 1: title，unit和table不在同一页上: 不能添加page header为title，到上一页检索最后一个block
# 忽略"/203"形式的页脚和“适用 不适用”
