import csv


def read_2d_csv_to_list(curr_file):
    analysis_list = []
    with open(curr_file) as f_analysis_file:
        data_reader = csv.reader(f_analysis_file, delimiter=",")
        analysis_list = list(data_reader)
    print(analysis_list)


read_2d_csv_to_list(
    "environment\\assets\Comm\matrix\\new_maze\\maze\\sector_maze_2d.csv"
)
