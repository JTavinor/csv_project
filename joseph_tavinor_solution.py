"""
Please write you name here: Joseph Tavinor
"""
import csv
import re


def process_shifts(path_to_csv: str) -> dict:
    """

    :param path_to_csv: The path to the work_shift.csv
    :type string:
    :return: A dictionary with time as key (string) with format %H:%M
        (e.g. "18:00") and cost as value (Number)
    For example, it should be something like :
    {
        "17:00": 50,
        "22:00: 40,
    }
    In other words, for the hour beginning at 17:00, labour cost was
    50 pounds
    :rtype dict:
    """
    # Reads csv as dictionary
    with open(path_to_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        shifts_dict = {}

        # Create entry for every hour
        for x in range(0, 24):
            shifts_dict[f'{x}:00'] = 0

        for line in csv_reader:
            # Split start and end time into hours and minutes
            start_time = re.search('([\d]+):([\d]+)', line['start_time'])
            start_hour = int(start_time.group(1))
            start_minute = int(start_time.group(2))

            end_time = re.search('([\d]+):([\d]+)', line['end_time'])
            end_hour = int(end_time.group(1))
            end_minute = int(end_time.group(2))

            # Split break time into hours and minutes
            break_time = re.search('([\d]+)[\.]?([\d]*)[A-z]*[\s]*[-]+[\s]*([\d]+)[\.]?([\d]*)[A-z]*',
                                   line['break_notes'])

            # Sets the break start hour, and converts it to 24 hour time if needed
            break_start_hour = int(break_time.group(1))
            if break_start_hour not in range(start_hour, end_hour):
                break_start_hour += 12

            # Sets the break start minute, setting it to 0 if not included in break notes
            if break_time.group(2) == '':
                break_start_minute = 0
            else:
                break_start_minute = int(break_time.group(2))

            # Same as above for break end time
            break_end_hour = int(break_time.group(3))
            if break_end_hour not in range(start_hour, end_hour):
                break_end_hour += 12

            if break_time.group(4) == '':
                break_end_minute = 0
            else:
                break_end_minute = int(break_time.group(4))

            pay_rate = float(line['pay_rate'])
            # Works out how long they worked for in each hour and updates wages for that hour
            for x in range(0, 24):
                # BREAKS
                # If they start a break partway through the hour
                if break_start_hour == x and x + 1 <= break_end_hour and break_start_minute != 0:
                    shifts_dict[f'{x}:00'] += ((60 - break_start_minute) / 60) * pay_rate
                # If their break starts the previous or current hour and finishes within the current hour
                elif break_start_hour <= x == break_end_hour:
                    shifts_dict[f'{x}:00'] += ((60 - break_end_minute) / 60) * pay_rate
                # If they break for the whole hour
                elif x in range(break_start_hour, break_end_hour):
                    shifts_dict[f'{x}:00'] += 0

                # START/END TIMES
                # If they finish partway through the hour
                elif end_hour == x and end_minute != 0:
                    shifts_dict[f'{x}:00'] += (end_minute / 60) * pay_rate
                # If they start partway through the hour
                elif start_hour == x and start_minute != 0:
                    shifts_dict[f'{x}:00'] += ((60 - start_minute) / 60) * pay_rate

                # If they work the whole hour
                elif start_hour <= x < end_hour:
                    shifts_dict[f'{x}:00'] += pay_rate

    return shifts_dict


def process_sales(path_to_csv: str) -> dict:
    """

       :param path_to_csv: The path to the transactions.csv
       :type string:
       :return: A dictionary with time (string) with format %H:%M as key and
       sales as value (string),
       and corresponding value with format %H:%M (e.g. "18:00"),
       and type float)
       For example, it should be something like :
       {
           "17:00": 250,
           "22:00": 0,
       },
       This means, for the hour beginning at 17:00, the sales were 250 dollars
       and for the hour beginning at 22:00, the sales were 0.

       :rtype dict:
       """
    # Reading csv file as dictionary
    with open(path_to_csv, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        sales_by_hour = {}
        # Create entry for each hour
        for x in range(0, 24):
            sales_by_hour[f'{x}:00'] = 0
        # Get the hour of each transaction and add the amount to corresponding hour in sales_by_hour
        for line in csv_reader:
            sale_hour = re.search('([\d]+):[\d]+', line['time'])
            sales_by_hour[f"{sale_hour.group(1)}:00"] += float(line['amount'])
        # Rounding to combat roundoff error
        for key, value in sales_by_hour.items():
            sales_by_hour[key] = round(value, 2)

    return sales_by_hour


def compute_percentage(shifts: dict, sales: dict) -> dict:
    percentages = {}
    for x in range(0, 24):
        # Gets labour costs and earnings for each hour
        labour = shifts[f'{x}:00']
        earnings = sales[f'{x}:00']
        # Protect against dividing by 0
        if labour == 0:
            percentages[f'{x}:00'] = 0
        # If no sales, input negative labour costs for that hour
        elif earnings == 0:
            percentages[f'{x}:00'] = -labour
        # Inputs labour costs as % of sales
        else:
            percentages[f'{x}:00'] = (labour / earnings) * 100

    return percentages


def best_and_worst_hour(percentages: dict) -> list:
    """

    Args:
    percentages: output of compute_percentage
    Return: list of strings, the first element should be the best hour,
    the second (and last) element should be the worst hour. Hour are
    represented by string with format %H:%M
    e.g. ["18:00", "20:00"]

    """
    # Splits percentages into hours that had sales and hours that had no sales
    hours_with_sales_dict = {}
    hours_without_sales_dict = {}
    for k, v in percentages.items():
        if v > 0:
            hours_with_sales_dict[k] = v
        else:
            hours_without_sales_dict[k] = v

    # Sets best_hour as hour with least wage expenditure if no sales that day OR the lowest % of wages vs sales
    if hours_with_sales_dict == {}:
        best_hour = max(hours_without_sales_dict, key=hours_without_sales_dict.get)
    else:
        best_hour = min(hours_with_sales_dict, key=hours_with_sales_dict.get)

    # Sets worst_hour as highest % of wages vs sales if there were sales every hour someone was working OR hour with
    # biggest wage expenditure if there was an hour people worked that had no sales
    if percentages[min(percentages, key=percentages.get)] >= 0:
        worst_hour = max(percentages, key=percentages.get)
    else:
        worst_hour = min(percentages, key=percentages.get)

    best_and_worst_list = [best_hour, worst_hour]

    return best_and_worst_list


def main(path_to_shifts, path_to_sales):
    """
    Do not touch this function, but you can look at it, to have an idea of
    how your data should interact with each other
    """

    shifts_processed = process_shifts(path_to_shifts)
    sales_processed = process_sales(path_to_sales)
    percentages = compute_percentage(shifts_processed, sales_processed)
    best_hour, worst_hour = best_and_worst_hour(percentages)
    return best_hour, worst_hour

if __name__ == '__main__':
    # You can change this to test your code, it will not be used
    path_to_sales = ""
    path_to_shifts = ""
    best_hour, worst_hour = main(path_to_shifts, path_to_sales)

# Please write you name here: Joseph Tavinor
