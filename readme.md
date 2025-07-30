# 虚拟社区多智能体系统框架

该源码用于模拟资源的制作生成、计算、结果分析。其中**LLMComm-concurrent**是框架的完整实现，**LLMdrill**为基于社区精神病应急处置培训软件编写的副本，**LLMComm-非二维地图实现**是框架的简化实现，免去了二维数组地图的使用，换用字典格式表示地图属性。

## 模拟准备

1. 设置环境变量

与运行相关的环境变量保存在`backend_server/utils.py`，包含大模型调用的API、模拟参数设置、文件保存位置。

```python
"""火山"""
api_key = "<api_key>"
base_url = "<base_url>"
# 以下两个变量的使用情况在run_prompt.py中的model_param参数中自行修改
specify_model = "<要调用的大模型>"  # "deepseek-v3-250324"
specify_CoT_model = "<要调用的推理大模型>"  # "deepseek-r1-250120"

"""火山 doubao embedding"""
emb_api_key = "<emb_api_key>"
emb_base_url = "<emb_base_url>"
emb_specify_model = "<emb_specify_model>"  # doubao-embedding-text-240715

"""文件路径"""
asserts_path = "environment/assets/Comm"
env_matrix = f"{asserts_path}/matrix"
storage_path = "environment/storage"
temp_storage_path = "environment/temp_storage"
prompt_path = "backend_server/persona/prompt_modules/templates"
survey_result_path = "environment/storage/survey_result"
# analysis相关
analysis_persona_path = "environment/storage/final_comm_30_1h/personas"
"""地图属性"""
collision_block_id = "20000"
outing_cell = (1000, 1000)  # 外出时角色坐标 设置为一个地图外的坐标
backing_cell = (79, 24)  # 外出返回时角色坐标

"""模拟设置"""
optimize_clone = True  # False:完全复制，True:只复制必要文件，建议设置为True
develop = False  # 打印过程信息

```

2. 生成运行地图

Excel制作的地图需要使用脚本处理。处理脚本位于`environment/assets/Comm/matrix/maze_design/maze_divide.py`，运行前将地图excel文件放置在`environment/assets/Comm/matrix/curr_maze`，命名为`final_maze_1.3.xlsx`；地图的属性-编码文件应放置在`environment/assets/Comm/matrix/curr_maze/blocks`

Excel地图制作格式要求：

- 每一个单元格以`object area sector`的顺序表示该坐标的位置信息
- 如果不包含`object`层级，则记录为`area sector`，以此类推
- 地图中的障碍用带颜色的单元格背景表示
- 属性-编码文件表示每个地图属性对应的id，用于二维地图寻址等操作。目前使用手动编写csv编码实现：
  - sector_id从10001开始编号，步长20
  - sector下的area_id从sector_id+1开始编号，步长1
  - area_id从11001编号，步长1
  - csv编写示例见`environment/assets/Comm/matrix/curr_maze/blocks`

3. 生成角色文件

运行`backend_server/batch_create_personas.py`生成角色文件，此过程需要调用大模型

4. 初次运行模拟前，需要制作初始模拟记录文件。请参考`environment/storage/final_comm`

```
origin_record
 -environment
  -0.json
 -movement
 -personas
  -persona0
  -persona1
  ...
 meta.json
```

## 运行模拟

1. 通过命令行运行

命令行模式下的运行命令请参考弹出窗口中的指令说明

```shell
python simulation.py normal origin(原始记录名称) target(目标记录名称)
```

2. 通过脚本运行

```shell
python simulation.py script origin target script_path(要执行的脚本文件路径)
```

## 脚本编写

规范如下：

```json
{
  "实验1":[
    {"type":"sec_per_step","sec_per_step":"10"},
    {"type":"load","func":"whisper","args":["whisper_csv文件路径","可批量执行多个文件"]},
    {"type":"run","day":"10"},
    {"type":"run","hour":"10"},
    {"type":"run","min":"10"},
    {"type":"run","step":"10"},
    {"type":"intervene","func":"chat","args":["发起人名称","chat对象","说话内容"]},
    {"type":"intervene","func":"contact","args":["发起人名称","chat对象","对话要求"]},
    {"type":"intervene","func":"broadcast","args":[["广播对象1","广播对象2"],"广播内容"]},
    {"type":"intervene","func":"whisper","args":[["植入对象1","植入对象2"],"植入内容"]},
    {"type":"intervene","func":"order","args":[["命令对象1","命令对象2"],"命令内容"]},
    {"type":"intervene","func":"action","args":[["动作对象1","动作对象2"],"动作内容"]},
    {"type":"interview","args":[["访谈对象1","访谈对象2"]]},
    {"type":"survey","args":[["调查对象1","调查对象2"],"调查问卷名称","对调查问卷要求","调查问卷路径"]},
    {"type":"save"},
  ]
}
```



## 实验分析

运行`backend_server/analysis`下相应的代码文件

## LLMdrill

运行以下指令开启Fastapi服务

```
uvicorn main:app --reload
```

api功能测试文件：test.http

功能说明文档链接：https://sweet-rotate-c30.notion.site/1cb20c639b6c80f2a3f6d53bb2666053?source=copy_link

## Acknowledgements

框架引用：https://github.com/joonspk-research/generative_agents