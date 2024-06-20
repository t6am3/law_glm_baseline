from zhipuai import ZhipuAI
from schema import database_schema


client = ZhipuAI(api_key="")


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

    return response


system_prompt = """
【任务要求】
你是一位专业的python开发工程师，你将根据用户的需求，使用python语言编写代码解决用户提出的问题。请仅仅返回python代码。
注意：
1. 你的代码必须使用python语言编写，并且必须符合python语法规范。
2. 你将使用已经编写好的python函数来解决用户的问题，不要使用已经提供好的函数或者内置函数之外的函数。
3. 你写好的代码将会被执行

【已经写好的python代码】
def http_api_call(api_name, data, max_data_len=None):
    url = f"{domain}/law_api/{api_name}"
    
    rsp = requests.post(url, json=data, headers=headers)
    final_rsp = rsp.json()
    final_rsp = [final_rsp] if isinstance(final_rsp, dict) else final_rsp
    
    if max_data_len is None:
        max_data_len = len(final_rsp)
    return {
        "return_items_count": len(final_rsp),
        "return": final_rsp[:max_data_len]
    }


def get_company_name_by_bref(bref):
    company_names = [i["公司名称"] for i in http_api_call("search_company_name_by_info", {"key": "公司简称", "value": bref})["return"]]
    return company_names


def get_company_name_by_en(bref):
    company_names = [i["公司名称"] for i in http_api_call("search_company_name_by_info", {"key": "英文名称", "value": bref})["return"]]
    return company_names


def augment_company_name(company_name):
    company_name = company_name if isinstance(company_name, list) else [company_name]
    for c in company_name[:]:
        company_name += get_company_name_by_bref(c)
        company_name += get_company_name_by_en(c)
        company_name += [c.replace("(", "（").replace(")", "）")]
        company_name += [c.replace("（", "(").replace("）", ")")]

    return list(set(company_name))


@register_tool
def get_company_info(
        company_name: Annotated[list, "公司名称或简称的列表", True],
) -> List[CompanyInfo]:
    '''
    根据公司名称获得该公司所有基本信息，可以传入多个公司名称，返回一个列表
    '''
    company_name = augment_company_name(company_name)
    return http_api_call("get_company_info", {"company_name": company_name})


@register_tool
def get_company_register(
        company_name: Annotated[list, "公司名称或简称的列表", True],
) -> List[CompanyRegister]:
    '''
    根据公司名称获得该公司所有注册信息，可以传入多个公司名称，返回一个列表
    '''
    company_name = augment_company_name(company_name)
    return http_api_call("get_company_register", {"company_name": company_name})


@register_tool
def get_sub_company_info(
        company_name: Annotated[list, "母公司名称的列表", True],
) -> SubCompanyInfo:
    '''
    根据母公司名称获得该母公司所有的关联投资、母公司等信息，可以传入多个母公司名称，返回一个列表
    '''
    company_name = augment_company_name(company_name)
    all_subs = company_name[:]
    for comp_name in company_name:
        # print("@@@", http_api_call("search_company_name_by_sub_info", {"key": "关联上市公司全称", "value": comp_name})["return"])
        all_subs += [i["公司名称"] for i in http_api_call("search_company_name_by_sub_info", {"key": "关联上市公司全称", "value": comp_name}, max_data_len=None)["return"]]
        # print("!", all_subs)
    print(all_subs)
    return http_api_call("get_sub_company_info", {"company_name": all_subs})

@register_tool
def get_sub_company_info_by_sub_comp(
        company_name: Annotated[list, "子公司名称的列表", True],
) -> SubCompanyInfo:
    '''
    根据子公司名称获得该子公司所有的关联投资等信息，可以传入多个子公司名称，返回一个列表
    '''
    company_name = augment_company_name(company_name)
    return http_api_call("get_sub_company_info", {"company_name": company_name})


@register_tool
def get_legal_document(
        case_num: Annotated[list, "案号", True],
) -> List[LegalDocument]:
    '''
    根据案号查询相关法律文书的内容，可以传入多个案号，返回一个列表
    '''
    return http_api_call("get_legal_document", {"case_num": case_num})


@register_tool
def search_company_name_by_info(
        key: Annotated[CompanyInfoEnum, "公司基本信息字段名称", True],
        value: Annotated[str, "公司基本信息字段具体的值", True],
) -> str:
    '''
    根据公司某个基本信息字段是某个值时，查询所有满足条件的公司名称
    '''
    return http_api_call("search_company_name_by_info", {"key": key, "value": value})


@register_tool
def search_company_name_by_register(
        key: Annotated[CompanyRegisterEnum, "公司注册信息字段名称", True],
        value: Annotated[str, "公司注册信息字段具体的值", True],
) -> str:
    '''
    根据公司某个注册信息字段是某个值时，查询所有满足条件的公司名称
    '''
    return http_api_call("search_company_name_by_register", {"key": key, "value": value})


@register_tool
def search_company_name_by_sub_info(
        key: Annotated[SubCompanyInfoEnum, "子公司融资信息字段名称", True],
        value: Annotated[str, "子公司融资信息信息字段具体的值", True],
) -> str:
    '''
    根据子公司融资信息字段是某个值时，查询所有满足条件的子公司名称
    '''
    return http_api_call("search_company_name_by_sub_info", {"key": key, "value": value})


@register_tool
def search_case_num_by_legal_document(
        key: Annotated[LegalDocumentEnum, "法律文书信息字段名称", True],
        value: Annotated[str, "法律文书信息字段具体的值", True],
) -> str:
    '''
    根据法律文书信息字段是某个值时，查询所有满足条件的法律文书案号
    '''
    return http_api_call("search_case_num_by_legal_document", {"key": key, "value": value})
【注意】仅仅输出python代码
"""
# 【可以查询到的数据库schema】
# """ + database_schema


def run(query, model="glm-4"):
    tools = [
        {
            "type": "function", 
            "function": {
                "name": "python_code_interpreter", 
                "description": "Python代码解释器", 
                "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]},
        }}]
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"【用户问题】{query}"},
    ]
    # print(messages)
    return call_glm(messages, model=model, tools=None)


if __name__ == "__main__":
    print(run("请问批发业注册资本最高的前3家公司的名称以及他们的注册资本（单位为万元）？", model="glm-4"))