import csv


def convert_1d_to_2d(input_file, output_file, num_cols):
    """
    将一维矩阵列表的CSV文件转换为二维矩阵并保存到新文件。

    参数：
    - input_file (str): 输入的CSV文件路径。
    - output_file (str): 输出的CSV文件路径。
    - num_cols (int): 二维矩阵的列数。
    """
    try:
        # 读取一维矩阵
        with open(input_file, "r") as infile:
            reader = csv.reader(infile)
            matrix_1d = next(reader)  # 假设只有一行

        # 转换为二维矩阵
        matrix_2d = [
            matrix_1d[i : i + num_cols] for i in range(0, len(matrix_1d), num_cols)
        ]

        # 写入二维矩阵到新的CSV文件
        with open(output_file, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(matrix_2d)

        print(f"转换完成！输出文件已保存到: {output_file}")

    except Exception as e:
        print(f"发生错误: {e}")


# 使用示例
if __name__ == "__main__":
    input_csv = "D:\Code\Workspace\LLMComm\LLMComm\environment\\assets\Comm\matrix\maze\spawning_location_maze.csv"  # 替换为你的输入文件路径
    output_csv = "D:\Code\Workspace\LLMComm\LLMComm\environment\\assets\Comm\matrix\maze\spawning_location_maze_2d.csv"  # 替换为你的输出文件路径
    num_columns = 140  # 替换为二维矩阵的列数
    convert_1d_to_2d(input_csv, output_csv, num_columns)
