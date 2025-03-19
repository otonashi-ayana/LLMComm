import sys
import os
import csv
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed
from create_persona import generate_persona_details, create_direct_memory_json

DEFAULT_PERSONA_PATH = "D:\Code\Workspace\LLMComm\LLMComm-Concurrent\environment\storage\create_test\personas"
DEFAULT_CSV_PATH = "D:\Code\Workspace\LLMComm\LLMComm-Concurrent\environment\storage\create_test\persona_templates.csv"


def process_persona(row, output_dir, index):
    """处理单个角色生成的函数"""
    try:
        name = row.get("姓名", "")
        gender = row.get("性别", "")
        age = row.get("年龄", "")
        occupation = row.get("职业", "")
        education_level = row.get("文化层次", "")
        background_and_personality = row.get("背景及性格特征", "")

        print(f"\n正在生成角色: {name}")

        # 生成角色详情
        persona_details = generate_persona_details(
            name,
            gender,
            age,
            occupation,
            education_level,
            background_and_personality,
        )

        if persona_details:
            # 获取化名（如果有）
            alias = persona_details.get("alias", "")
            actual_name = alias if alias and alias.strip() else name

            # 创建角色目录
            persona_dir = os.path.join(output_dir, actual_name)
            os.makedirs(persona_dir, exist_ok=True)

            # 创建直接记忆文件
            output_path = os.path.join(persona_dir, "direct_memory.json")
            create_direct_memory_json(
                persona_details, output_path, name, gender, age, actual_name
            )
            print(f"已成功创建角色: {actual_name}")

            # 返回成功的结果、索引和详细信息
            return {
                "success": True,
                "index": index,
                "name": name,
                "alias": alias if alias and alias.strip() else None,
                "personality": persona_details.get("personality", ""),
                "background": persona_details.get("background", ""),
                "living_area": persona_details.get("living_area", ""),
                "life_style": persona_details.get("life_style", ""),
                "daily_plan_desc": persona_details.get("daily_plan_desc", ""),
            }
        else:
            print(f"生成角色 {name} 的信息失败")
            return {"success": False, "index": index, "name": name}

    except Exception as e:
        print(f"处理角色 {row.get('姓名', '')} 时出错: {e}")
        return {"success": False, "index": index, "name": row.get("姓名", "")}


def batch_create_personas(csv_file, output_dir, max_workers=4):
    """从CSV文件批量创建角色，使用多线程并发处理"""
    print(f"正在从 {csv_file} 读取角色信息...")

    # 读取原始CSV数据
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames.copy() if reader.fieldnames else []

    # 确保有所有需要的字段
    required_fields = [
        "化名",
        "性格特点",
        "背景信息",
        "居住区域",
        "生活方式",
        "日常计划",
    ]
    existing_fields = set(fieldnames)

    # 如果缺少字段，则添加
    for field in required_fields:
        if field not in existing_fields:
            fieldnames.append(field)

    # 使用线程池并发生成角色
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_row = {
            executor.submit(process_persona, row, output_dir, i): i
            for i, row in enumerate(rows)
        }

        # 收集结果
        for future in as_completed(future_to_row):
            result = future.result()
            if result:
                results.append(result)

    # 处理结果，更新字段
    fields_updated = False
    for result in results:
        if result["success"]:
            index = result["index"]
            if "alias" in result and result["alias"]:
                rows[index]["化名"] = result["alias"]
                fields_updated = True
            if "personality" in result:
                rows[index]["性格特点"] = result["personality"]
                fields_updated = True
            if "background" in result:
                rows[index]["背景信息"] = result["background"]
                fields_updated = True
            if "living_area" in result:
                rows[index]["居住区域"] = result["living_area"]
                fields_updated = True
            if "life_style" in result:
                rows[index]["生活方式"] = result["life_style"]
                fields_updated = True
            if "daily_plan_desc" in result:
                rows[index]["日常计划"] = result["daily_plan_desc"]
                fields_updated = True

    # 如果有更新的字段，写回CSV文件
    if fields_updated:
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            print(f"\n已将生成的角色详细信息更新回文件: {csv_file}")

    print("\n批量生成角色完成!")


def main():
    parser = argparse.ArgumentParser(description="批量生成角色记忆文件")
    parser.add_argument(
        "--csv_file",
        default=DEFAULT_CSV_PATH,
        type=str,
        help="包含角色信息的CSV文件路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_PERSONA_PATH,
        help="输出目录路径",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="并发工作线程数",
    )

    args = parser.parse_args()

    # 调用批量生成函数，传入并发线程数
    batch_create_personas(args.csv_file, args.output, args.workers)


if __name__ == "__main__":
    main()
