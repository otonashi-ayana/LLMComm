import datetime

prompt = """这是李四原本计划在 10:00 AM 到 14:00 PM 之间的日程安排。
10:00 ~ 10:10 -- 营业李四饭店（从住处步行至李四饭店）
10:10 ~ 10:15 -- 营业李四饭店（检查店内桌椅摆放）
10:15 ~ 10:20 -- 营业李四饭店（开启店内照明和空调设备）
10:20 ~ 10:30 -- 营业李四饭店（与提前到店的顾客进行简单寒暄）    
10:30 ~ 10:40 -- 营业李四饭店（从冷库取出肉类食材进行解冻处理）  
10:40 ~ 10:50 -- 营业李四饭店（清洗蔬菜并切配装盘）
10:50 ~ 10:55 -- 营业李四饭店（接收第一批顾客的点单需求）        
10:55 ~ 11:00 -- 营业李四饭店（在厨房准备首批待烹饪的食材）      
11:00 ~ 11:15 -- 营业李四饭店（专注烹饪食材）
11:15 ~ 11:20 -- 营业李四饭店（将烹饪好的菜品分装到餐盘）        
11:20 ~ 11:30 -- 营业李四饭店（亲自为顾客端送餐品）
11:30 ~ 11:35 -- 营业李四饭店（主动询问顾客是否需要添加饮品）    
11:35 ~ 11:40 -- 营业李四饭店（返回厨房清理残余食材）
11:40 ~ 11:45 -- 营业李四饭店（接收新顾客的点单需求）
11:45 ~ 11:55 -- 营业李四饭店（准备第二批烹饪食材）
11:55 ~ 12:10 -- 营业李四饭店（继续烹饪新订单的菜品）
12:10 ~ 12:15 -- 营业李四饭店（核对上午营收）
12:15 ~ 12:25 -- 营业李四饭店（补充消耗殆尽的调料罐）
12:25 ~ 12:30 -- 营业李四饭店（更换厨房的砧板）
12:30 ~ 12:35 -- 营业李四饭店（处理特殊顾客的加辣需求）
12:35 ~ 12:45 -- 营业李四饭店（擦拭顾客用餐完毕的桌面）
12:45 ~ 12:50 -- 营业李四饭店（检查后厨冰箱的食材存量）
12:50 ~ 12:55 -- 营业李四饭店（安排帮工准备下午所需食材）        
12:55 ~ 13:00 -- 营业李四饭店（短暂休息补充体力）
13:00 ~ 13:05 -- 营业李四饭店（接收第三批顾客的点单需求）        
13:05 ~ 13:15 -- 营业李四饭店（准备第三批烹饪食材）
13:15 ~ 13:30 -- 营业李四饭店（继续烹饪新订单的菜品）
13:30 ~ 13:35 -- 营业李四饭店（将烹饪好的菜品分装到餐盘）        
13:35 ~ 13:45 -- 营业李四饭店（亲自为顾客端送餐品）
13:45 ~ 13:50 -- 营业李四饭店（主动询问顾客是否需要添加饮品）    
13:50 ~ 13:55 -- 营业李四饭店（返回厨房清理残余食材）
13:55 ~ 14:00 -- 营业李四饭店（短暂休息补充体力）


但李四意外地进行了营业李四饭店（谈论有关 李四用新调料为李华烹饪红烧肉的对话。），持续了1分钟。请根据此情况，将李四从10:00 AM到14:00 PM的日程进行相应调整（必须在14:00 PM之前结束）。(仅输出日程安排内容，禁止添加其他任何解释、总结或附加内容)
调整后的日程安排（仅输出变更时段之后的调整部分，即从以下日程结尾 的下一项开始）：
10:00 ~ 10:10 -- 营业李四饭店（从住处步行至李四饭店）
10:10 ~ 10:15 -- 营业李四饭店（检查店内桌椅摆放）
10:15 ~ 10:20 -- 营业李四饭店（开启店内照明和空调设备）
10:20 ~ 10:30 -- 营业李四饭店（与提前到店的顾客进行简单寒暄）    
10:30 ~ 10:40 -- 营业李四饭店（从冷库取出肉类食材进行解冻处理）  
10:40 ~ 10:50 -- 营业李四饭店（清洗蔬菜并切配装盘）
10:50 ~ 10:55 -- 营业李四饭店（接收第一批顾客的点单需求）        
10:55 ~ 11:00 -- 营业李四饭店（在厨房准备首批待烹饪的食材）      
11:00 ~ 11:15 -- 营业李四饭店（专注烹饪食材）
11:15 ~ 11:20 -- 营业李四饭店（将烹饪好的菜品分装到餐盘）        
11:20 ~ 11:30 -- 营业李四饭店（亲自为顾客端送餐品）
11:30 ~ 11:35 -- 营业李四饭店（主动询问顾客是否需要添加饮品）    
11:35 ~ 11:40 -- 营业李四饭店（返回厨房清理残余食材）
11:40 ~ 11:45 -- 营业李四饭店（接收新顾客的点单需求）
11:45 ~ 11:55 -- 营业李四饭店（准备第二批烹饪食材）
11:55 ~ 12:10 -- 营业李四饭店（继续烹饪新订单的菜品）
12:10 ~ 12:15 -- 营业李四饭店（核对上午营收）
12:15 ~ 12:25 -- 营业李四饭店（补充消耗殆尽的调料罐）
12:25 ~ 12:25 -- 营业李四饭店（即将去 更换厨房的砧板）
12:25 ~ 12:26 -- 营业李四饭店（谈论有关 李四用新调料为李华烹饪红 烧肉的对话。）
(从此处开始，仅生成后续日程)"""
response = """"""


def response_clean(response, prompt):
    new_schedule = prompt.split("(从此处开始，仅生成后续日程)")[0] + response.strip()
    new_schedule = new_schedule.split(
        "调整后的日程安排（仅输出变更时段之后的调整部分，即从以下日程结尾的下一项开始）："
    )[-1].strip()
    # print(new_schedule)
    new_schedule = new_schedule.strip().split("\n")
    # print(len(new_schedule))

    ret_temp = []
    for i in new_schedule:
        ret_temp += [i.split(" -- ")]

    ret = []
    for time_str, action in ret_temp:
        start_time = time_str.split(" ~ ")[0].strip()
        end_time = time_str.split(" ~ ")[1].strip()
        delta = datetime.datetime.strptime(
            end_time, "%H:%M"
        ) - datetime.datetime.strptime(start_time, "%H:%M")
        delta_min = int(delta.total_seconds() / 60)
        if delta_min < 0:
            delta_min = 0
        ret += [[action, delta_min]]

    return ret


def response_validate(response, prompt=""):
    try:
        response = response_clean(response, prompt)
        # print(response)
        dur_sum = 0
        for act, dur in response:
            dur_sum += dur
            # print(dur, act)
            if str(type(act)) != "<class 'str'>":
                print(f"<run_prompt_new_decomp_schedule> act error: {act}")
                return False
            if str(type(dur)) != "<class 'int'>":
                print(f"<run_prompt_new_decomp_schedule> dur error: {dur}")
                return False
        x = prompt.split("\n")[0].split("原本计划在")[-1].strip()[:-1]
        x_start = datetime.datetime.strptime(x.split("到")[0].strip(), "%H:%M %p")
        x_end = datetime.datetime.strptime(
            x.split("到")[-1].rsplit(" ", 1)[0].strip(), "%H:%M %p"
        )
        delta_min = int((x_end - x_start).total_seconds() / 60)

        if int(dur_sum) != int(delta_min):
            print(
                f"<run_prompt_new_decomp_schedule> error dur_sum != delta_min: {dur_sum} != {delta_min}"
            )
            return False

    except:
        return False
    return True


print(response_validate(response, prompt))
# print(prompt.split("(从此处开始，生成后续日程)"))
