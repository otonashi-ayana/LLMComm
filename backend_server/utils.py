"""百炼"""

api_key = "sk-f690a69ebfdd4298a8c7ef763c42de28"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
specify_model = "deepseek-v3"
# specify_model_v3 = "deepseek-v3"
# specify_model_r1 = "deepseek-r1"
# specify_model = "qwen-plus"

"""embedding"""
emb_api_key = "sk-f690a69ebfdd4298a8c7ef763c42de28"
emb_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
emb_specify_model = "text-embedding-v3"

"""deepseek"""
# api_key = "sk-e4073b1a2bed4b7b817d8a32b5cdec3d"
# base_url = "https://api.deepseek.com"
# specify_model = "deepseek-chat"

maze_assets_loc = "D:/Code/Workspace/LLMComm/LLMComm/environment/assets"
env_matrix = f"{maze_assets_loc}/Comm/matrix/curr_maze"
# env_visuals = f"{maze_assets_loc}/Comm/visuals"

storage_path = "D:/Code/Workspace/LLMComm/LLMComm/environment/storage"
temp_storage_path = "D:/Code/Workspace/LLMComm/LLMComm/environment/temp_storage"
prompt_path = (
    "D:/Code/Workspace/LLMComm/LLMComm/backend_server/persona/prompt_modules/templates"
)

log_file = f"{storage_path}/output.log"

collision_block_id = 20000
outing_cell = (1000, 1000)
backing_cell = (80, 24)


debug = True
develop = False
simple_log = True
