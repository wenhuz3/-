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
        # 如果第一行中有占位超过一行的cell（一般是第一行第一列），说明是多层级table
        if cell["start_row"] == 0 and cell["end_row"] > cell["start_row"]:
            multi_row_header = True
            header_rows.extend(range(cell["start_row"], cell["end_row"] + 1))
            break  # Exit loop once a multi-row header is found

    # Process each cell in the table
    for line in table["table_cells"]:
        # Handle multi-row headers
        if multi_row_header:
            if line["start_row"] in header_rows:
                # 确保 output["header"] 列表的长度足以包含到当前单元格的结束行
                while len(output["header"]) <= line["end_row"]:
                    output["header"].append([])
                # 遍历当前单元格覆盖的所有行，处理跨行的情况
                for header_row in range(line["start_row"], line["end_row"] + 1):
                    # 确保每一行的长度足以包含到当前单元格的结束列
                    while len(output["header"][header_row]) <= line["end_col"]:
                        output["header"][header_row].append("")
                    # 遍历当前cell覆盖的所有列
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

        # Handle key index
        if (
            line["start_row"] > 0
            and line["start_col"] == 0
            and not line["start_row"] in header_rows
        ):
            output["key_index"].append(line["text"].replace("\n", ""))
        # Handle values
        elif line["start_row"] > 0 and line["start_col"] != 0 and not line["start_row"] in header_rows:
            # 如果换行了则append一行的values
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

        # search reversely in the element before the table to find unit
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
                    if "单位:" not in title and "币种:" not in title and "2021年年度报告" not in title
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
                # get the first block on the page that is not header
                previous_table_lines = [
                    line["text"] for line in current_tables[0]["lines"]
                ]
                # 如果table前只有页眉则判定为连续table
                if (
                    len(previous_table_lines) == 1
                    and "2021年年度报告" in previous_table_lines[0]
                ):
                    # Skip processing this table as it's the second half of table in the previous page
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
                prev_col = 0
                values = []
                for line in next_tables[1]["table_cells"]:
                  # Handle key index
                  if (
                      line["start_row"] > 0
                      and line["start_col"] == 0
                  ):
                      output["key_index"].append(line["text"].replace("\n", ""))
                  # Handle values
                  elif line["start_row"] > 0 and line["start_col"] != 0:
                      # 如果换行了则append一行的values
                      if prev_col >= line["start_col"]:
                          if values:  # Only append if values are non-empty
                              output["values"].append(values)
                          values = []
                      values.append(line["text"].replace("\n", ""))
                      prev_col = line["start_col"]

                # Ensure the last set of values is added
                if values:
                    output["values"].append(values)

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
