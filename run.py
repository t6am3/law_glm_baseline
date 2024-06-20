from tools import get_tools, dispatch_tool
from utils import multi_thread_excute
from zhipuai import ZhipuAI
from pprint import pprint
import json
import logging
import time
from schema import database_schema


client = ZhipuAI(api_key="") # 填写你的API Key

system_prompt = """你是一位金融法律专家，你的任务是根据用户给出的query，调用给出的工具接口，获得用户想要查询的答案。
所提供的工具接口可以查询四张数据表的信息，数据表的schema如下:
""" + database_schema


def call_glm(messages, model="glm-4",
             temperature=0.95,
             tools=None):
    response = client.chat.completions.create(
        model=model,  # 填写需要调用的模型名称
        messages=messages,
        temperature=temperature,
        top_p=0.9,
        tools=tools,
    )
    # print(messages)
    print(response.json())
    return response


def run(query, tools):
    tokens_count = 0
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    for i in range(10):
        print(f"##第{i}轮对话##")
        pprint(messages)
        print("#" * 10)
        print("\n")

        for _ in range(3):
            try:
                response = call_glm(messages, tools=tools)
                tokens_count += response.usage.total_tokens
                messages.append(response.choices[0].message.model_dump())
                break
            except Exception as e:
                print(e)
                
        try:
            if response.choices[0].finish_reason == "tool_calls":
                tools_call = response.choices[0].message.tool_calls[0]
                tool_name = tools_call.function.name
                args = tools_call.function.arguments
                obs = dispatch_tool(tool_name, args, "007")
                messages.append({
                    "role": "tool", 
                    "content": f"{obs}",
                    "tool_id": tools_call.id
                })
            else:
                print("###对话结束###")
                break
        except Exception as e:
            messages = [
                {"role": "system", "content": "你是一个法律专家，请根据你的专业知识回答用户的问题"},
                {"role": "user", "content": query}
            ]
            response = call_glm(messages, tools=None)
            return tokens_count, [{"content": response.choices[0].message.content, "role": "assistant"}], None
        
    return tokens_count, messages, response


def run_all():
    tools = get_tools()
    start = time.time()
    # pprint(tools)

    # 读取lines
    lines = [i for i in open("./question_junior_A.json", "r", encoding="utf-8").readlines() if i.strip()]

    def task(line):
        line = json.loads(line)
        query = line["question"]

        tokens_count, messages, response = run(query, tools)
        ans = messages[-1]["content"]
        return tokens_count, {
            "id": line["id"],
            "question": query,
            "answer": ans
        }

    all_results = multi_thread_excute([[task, line] for line in lines], 20)
    all_tokens_count = sum([i[0] for i in all_results])
    print("使用tokens总数：", all_tokens_count, "用时", time.time() - start, "s")
    all_results_json = sorted([i[1] for i in all_results], key=lambda x: x["id"])
    open("./evaluate/sub.json", "w", encoding="utf-8").write("\n".join([json.dumps(line, ensure_ascii=False) for line in all_results_json]))


if __name__ == '__main__':
    # print(get_tools())
    print(run("350781100073458注册的企业名称。", tools=get_tools())[1])
    # run_all()